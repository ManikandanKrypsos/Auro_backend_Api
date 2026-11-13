import stripe
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminOrReception
import logging

logger = logging.getLogger(__name__)
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils.decorators import method_decorator

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')


class CreateCheckoutSessionView(APIView):
    """
    POST /api/payments/create-checkout-session/
    For web payments only (flutter web using url_launcher)
    Body: { "appointment_id": 34 }

    Response:
    {
        "checkout_url": "https://checkout.stripe.com/pay/cs_test_xxx",
        "session_id": "cs_test_xxx"
    }
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request):
        from appointments.models import Appointment

        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response({'error': 'appointment_id is required.'}, status=400)

        try:
            appt = Appointment.objects.select_related(
                'patient', 'treatment', 'price_plan', 'staff'
            ).get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        if appt.payment_status == 'paid':
            return Response({'error': 'This appointment is already paid.'}, status=400)

        # Get amount
        amount = None
        if appt.price_plan and appt.price_plan.price:
            amount = appt.price_plan.price
        elif appt.payment_amount:
            amount = appt.payment_amount
        elif appt.treatment and appt.treatment.price:
            amount = appt.treatment.price

        if not amount:
            return Response({'error': 'No price set for this appointment.'}, status=400)

        amount_cents = int(float(amount) * 100)

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency':     'eur',
                        'unit_amount':  amount_cents,
                        'product_data': {
                            'name':        appt.treatment.name if appt.treatment else 'Treatment',
                            'description': f"Patient: {appt.patient.name if appt.patient else ''} | Therapist: {appt.staff.username if appt.staff else ''}",
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://krypsos-auro.onrender.com/#/paymentSuccessScreen?appointment_id=' + str(appt.id),
                cancel_url='https://krypsos-auro.onrender.com/#/paymentCancelScreen?appointment_id=' + str(appt.id),
                metadata={
                    'appointment_id': str(appt.id),
                    'patient_name':   appt.patient.name if appt.patient else '',
                    'treatment_name': appt.treatment.name if appt.treatment else '',
                },
            )

            # Update appointment payment info
            appt.payment_amount = amount
            appt.payment_type   = 'online'
            appt.payment_status = 'pending'
            appt.save()

            return Response({
                'checkout_url': session.url,
                'session_id':   session.id,
                'appointment_id': appt.id,
                'amount_display': f"€{float(amount):.2f}",
            })

        except stripe.error.StripeError as e:
            logger.warning('Stripe error: %s', e)
            return Response({'error': getattr(e, 'user_message', None) or 'Payment provider error. Please try again.'}, status=400)


class CreatePaymentIntentView(APIView):
    """
    POST /api/payments/create-intent/
    Body: { "appointment_id": 42 }
    Returns client_secret for Flutter Stripe SDK
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request):
        from appointments.models import Appointment

        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response({'error': 'appointment_id is required.'}, status=400)

        try:
            appt = Appointment.objects.select_related(
                'patient', 'treatment', 'price_plan', 'staff'
            ).get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        if appt.payment_status == 'paid':
            return Response({'error': 'This appointment is already paid.'}, status=400)

        amount = None
        if appt.price_plan and appt.price_plan.price:
            amount = appt.price_plan.price
        elif appt.payment_amount:
            amount = appt.payment_amount
        elif appt.treatment and appt.treatment.price:
            amount = appt.treatment.price

        if not amount:
            return Response({'error': 'No price set for this appointment.'}, status=400)

        amount_cents = int(float(amount) * 100)

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='eur',
                metadata={
                    'appointment_id': str(appt.id),
                    'patient_name':   appt.patient.name if appt.patient else '',
                    'treatment_name': appt.treatment.name if appt.treatment else '',
                },
                description=f"Aura Clinic — {appt.treatment.name if appt.treatment else 'Treatment'} for {appt.patient.name if appt.patient else 'Patient'}",
            )

            appt.payment_amount = amount
            appt.payment_type   = 'online'
            appt.payment_status = 'pending'
            appt.save()

            return Response({
                'client_secret':     intent.client_secret,
                'payment_intent_id': intent.id,
                'amount':            amount_cents,
                'amount_display':    f"€{float(amount):.2f}",
                'currency':          'eur',
                'appointment_id':    appt.id,
                'patient':           appt.patient.name if appt.patient else '',
                'treatment':         appt.treatment.name if appt.treatment else '',
            })

        except stripe.error.StripeError as e:
            logger.warning('Stripe error: %s', e)
            return Response({'error': getattr(e, 'user_message', None) or 'Payment provider error. Please try again.'}, status=400)


class ConfirmPaymentView(APIView):
    """
    POST /api/payments/confirm/
    Body: { "appointment_id": 42, "payment_intent_id": "pi_xxx" }
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request):
        from appointments.models import Appointment

        appointment_id    = request.data.get('appointment_id')
        payment_intent_id = request.data.get('payment_intent_id')

        if not appointment_id or not payment_intent_id:
            return Response({'error': 'appointment_id and payment_intent_id are required.'}, status=400)

        try:
            appt = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == 'succeeded':
                appt.payment_status = 'paid'
                appt.payment_type   = 'online'
                appt.save()
                return Response({
                    'success':        True,
                    'message':        'Payment confirmed successfully.',
                    'appointment_id': appt.id,
                    'payment_status': appt.payment_status,
                    'amount_paid':    f"€{float(appt.payment_amount):.2f}" if appt.payment_amount else '',
                })
            else:
                return Response({'success': False, 'message': f"Payment not completed. Status: {intent.status}"}, status=400)

        except stripe.error.StripeError as e:
            logger.warning('Stripe error: %s', e)
            return Response({'error': getattr(e, 'user_message', None) or 'Payment provider error. Please try again.'}, status=400)


class RefundPaymentView(APIView):
    """
    POST /api/payments/refund/
    Body: { "appointment_id": 42 }
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request):
        from appointments.models import Appointment

        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response({'error': 'appointment_id is required.'}, status=400)

        try:
            appt = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        if appt.payment_status != 'paid':
            return Response({'error': 'This appointment has no completed payment to refund.'}, status=400)

        # Cash payment — no Stripe, just update DB
        if appt.payment_type == 'cash':
            appt.payment_status = 'refunded'
            appt.status         = 'cancelled'
            appt.save()
            return Response({
                'success':        True,
                'message':        'Cash payment refunded successfully.',
                'appointment_id': appt.id,
                'note':           'Cash refund — please return money manually to patient.',
            })

        # Online payment — refund via Stripe
        try:
            # First check if payment_intent_id stored in notes (web checkout)
            payment_intent_id = None
            if appt.notes and appt.notes.startswith('stripe_pi:'):
                payment_intent_id = appt.notes.split('stripe_pi:')[1].strip()

            # If not in notes, search Stripe
            if not payment_intent_id:
                intents = stripe.PaymentIntent.list(limit=100)
                for intent in intents.data:
                    if intent.metadata.get('appointment_id') == str(appt.id):
                        payment_intent_id = intent.id
                        break

            if not payment_intent_id:
                return Response({'error': 'Payment record not found in Stripe.'}, status=404)

            refund = stripe.Refund.create(payment_intent=payment_intent_id)

            if refund.status == 'succeeded':
                appt.payment_status = 'refunded'
                appt.status         = 'cancelled'
                appt.save()
                return Response({
                    'success':        True,
                    'message':        'Refund processed successfully.',
                    'refund_id':      refund.id,
                    'appointment_id': appt.id,
                })
            else:
                return Response({'error': f"Refund failed: {refund.status}"}, status=400)

        except stripe.error.StripeError as e:
            logger.warning('Stripe error: %s', e)
            return Response({'error': getattr(e, 'user_message', None) or 'Payment provider error. Please try again.'}, status=400)


class PaymentStatusView(APIView):
    """
    GET /api/payments/status/<appointment_id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        from appointments.models import Appointment
        try:
            appt = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        return Response({
            'appointment_id': appt.id,
            'payment_status': appt.payment_status,
            'payment_type':   appt.payment_type,
            'payment_amount': str(appt.payment_amount) if appt.payment_amount else None,
            'amount_display': f"€{float(appt.payment_amount):.2f}" if appt.payment_amount else None,
        })


# payment_type stored on the appointment → method shown in the UI
PAYMENT_METHOD_MAP = {'online': 'card', 'cash': 'cash'}
PAYMENT_METHODS    = ('card', 'transfer', 'cash', 'other')


def _trend(current, previous):
    if previous == 0:
        pct   = 100.0 if current > 0 else 0.0
        trend = 'up' if current > 0 else 'neutral'
    else:
        pct   = round((current - previous) / previous * 100, 1)
        trend = 'up' if pct > 0 else ('down' if pct < 0 else 'neutral')
    return {'value': current, 'change_pct': abs(pct), 'trend': trend}


def _pcts(values):
    """Whole-number percentages that add up to 100 (largest remainder)."""
    total = sum(values)
    if total <= 0:
        return [0] * len(values)
    raw    = [v * 100 / total for v in values]
    floors = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)[:100 - sum(floors)]:
        floors[i] += 1
    return floors


def _payment_totals(qs):
    from django.db.models import Sum, Count, Q
    agg = qs.aggregate(
        total=Count('id'),
        paid_count=Count('id', filter=Q(payment_status='paid')),
        pending_count=Count('id', filter=Q(payment_status='pending')),
        total_paid=Sum('payment_amount', filter=Q(payment_status='paid')),
        total_pending=Sum('payment_amount', filter=Q(payment_status='pending')),
    )
    return {
        'total':         agg['total'],
        'paid_count':    agg['paid_count'],
        'pending_count': agg['pending_count'],
        'total_paid':    round(float(agg['total_paid'] or 0), 2),
        'total_pending': round(float(agg['total_pending'] or 0), 2),
    }


class PaymentListView(APIView):
    """
    GET /api/payments/
      ?status=paid|pending|refunded     ?search=john       ?sort=date_desc|date_asc
      ?today=true
      ?month=2026-11                    (calendar month, by appointment date)
      ?date_from=2026-11-01&date_to=2026-11-30   (inclusive; used when month is not sent)
      ?staff_id=4                       (professional)
      ?page=1&page_size=20              (optional pagination, max 100)

    stats follow the period (month / date range / today) and staff filters,
    not status/search. change_pct compares with the previous period of the
    same length (previous month, previous N days, yesterday). With no period,
    stats are all-time compared with everything before the 1st of this month.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        import datetime
        from django.core.paginator import Paginator
        from django.utils import timezone
        from django.utils.dateparse import parse_date
        from appointments.models import Appointment

        p      = request.query_params
        status = p.get('status', '').strip().lower()
        search = p.get('search', '').strip()
        sort   = p.get('sort', 'date_desc').strip()
        today  = p.get('today', '').strip().lower() == 'true'
        errors = {}

        # ── Period ────────────────────────────────────────────────────────────
        period_start = period_end = None          # local dates, end inclusive
        month = p.get('month', '').strip()
        if month:
            try:
                y, m = map(int, month.split('-'))
                period_start = datetime.date(y, m, 1)
                period_end   = (datetime.date(y + (m == 12), m % 12 + 1, 1) - datetime.timedelta(days=1))
            except (ValueError, TypeError):
                errors['month'] = 'Use YYYY-MM.'
        elif p.get('date_from') or p.get('date_to'):
            period_start = parse_date(p.get('date_from', '')) if p.get('date_from') else None
            period_end   = parse_date(p.get('date_to', '')) if p.get('date_to') else None
            if p.get('date_from') and not period_start:
                errors['date_from'] = 'Use YYYY-MM-DD.'
            if p.get('date_to') and not period_end:
                errors['date_to'] = 'Use YYYY-MM-DD.'
        elif today:
            period_start = period_end = timezone.localdate()

        staff_id = None
        if p.get('staff_id'):
            try:
                staff_id = int(p['staff_id'])
            except ValueError:
                errors['staff_id'] = 'Must be an integer.'
        if errors:
            return Response(errors, status=400)

        def day_start(d):
            return timezone.make_aware(datetime.datetime.combine(d, datetime.time.min))

        def in_period(qs, start, end):
            if start:
                qs = qs.filter(date_time__gte=day_start(start))
            if end:
                qs = qs.filter(date_time__lt=day_start(end + datetime.timedelta(days=1)))
            return qs

        from .metrics import billable
        base = billable(Appointment.objects.all())
        if staff_id is not None:
            base = base.filter(staff_id=staff_id)

        # ── List ──────────────────────────────────────────────────────────────
        qs = in_period(base, period_start, period_end).select_related('patient', 'treatment', 'staff')
        if status in ['paid', 'pending', 'refunded']:
            qs = qs.filter(payment_status=status)
        if search:
            qs = qs.filter(patient__name__icontains=search)
        qs = qs.order_by('date_time' if sort == 'date_asc' else '-date_time')

        paginate = 'page' in p or 'page_size' in p
        if paginate:
            try:
                page_size = max(1, min(int(p.get('page_size') or 20), 100))
                page_num  = int(p.get('page') or 1)
            except ValueError:
                return Response({'page': 'page and page_size must be integers.'}, status=400)
            paginator = Paginator(qs, page_size)
            page      = paginator.get_page(page_num)
            items, count, total_pages, page_num = page.object_list, paginator.count, paginator.num_pages, page.number
        else:
            items = list(qs)
            count, total_pages, page_num, page_size = len(items), 1, 1, len(items)

        result = []
        for appt in items:
            local_dt = timezone.localtime(appt.date_time) if appt.date_time else None
            staff    = appt.staff
            result.append({
                'appointment_id': appt.id,
                'patient_name':   appt.patient.name if appt.patient else '',
                'treatment_name': appt.treatment.name if appt.treatment else '',
                'date':           local_dt.strftime('%b %d, %Y') if local_dt else '',
                'date_iso':       local_dt.date().isoformat() if local_dt else None,
                'amount':         f"€{float(appt.payment_amount):.2f}" if appt.payment_amount else '€0.00',
                'amount_value':   float(appt.payment_amount or 0),
                'payment_status': appt.payment_status,
                'payment_type':   appt.payment_type,
                'payment_method': PAYMENT_METHOD_MAP.get(appt.payment_type, 'other'),
                'staff_id':       staff.id if staff else None,
                'staff_name':     (staff.username or staff.email.split('@')[0]) if staff else None,
            })

        # ── Stats + previous period ───────────────────────────────────────────
        if period_start and period_end:
            if month:
                prev_end   = period_start - datetime.timedelta(days=1)
                prev_start = prev_end.replace(day=1)
            else:
                length     = (period_end - period_start).days + 1
                prev_end   = period_start - datetime.timedelta(days=1)
                prev_start = prev_end - datetime.timedelta(days=length - 1)
            cur_qs, prev_qs = in_period(base, period_start, period_end), in_period(base, prev_start, prev_end)
        else:
            # open-ended or no period → compare with everything before this month
            som = timezone.localdate().replace(day=1)
            cur_qs  = in_period(base, period_start, period_end)
            prev_qs = in_period(base, period_start, None).filter(date_time__lt=day_start(som))
        cur, prev = _payment_totals(cur_qs), _payment_totals(prev_qs)

        billed = cur['total_paid'] + cur['total_pending']
        paid_pct, pending_pct = _pcts([cur['total_paid'], cur['total_pending']])

        # Methods: paid payments only, share of count
        method_counts = {m: 0 for m in PAYMENT_METHODS}
        method_amount = {m: 0.0 for m in PAYMENT_METHODS}
        for ptype, amount in cur_qs.filter(payment_status='paid').values_list('payment_type', 'payment_amount'):
            m = PAYMENT_METHOD_MAP.get(ptype, 'other')
            method_counts[m] += 1
            method_amount[m] += float(amount or 0)
        method_pcts = dict(zip(PAYMENT_METHODS, _pcts([method_counts[m] for m in PAYMENT_METHODS])))

        return Response({
            'count':       count,
            'page':        page_num,
            'page_size':   page_size,
            'total_pages': total_pages,
            'payments':    result,
            'stats': {
                **{k: _trend(cur[k], prev[k]) for k in ('total', 'paid_count', 'pending_count', 'total_paid', 'total_pending')},
                'total_billed': round(billed, 2),
                'paid_pct':     paid_pct,
                'pending_pct':  pending_pct,
            },
            'payment_methods': method_pcts,
            'payment_methods_detail': {
                m: {'count': method_counts[m], 'amount': round(method_amount[m], 2)} for m in PAYMENT_METHODS
            },
            'period': {
                'from': str(period_start) if period_start else None,
                'to':   str(period_end) if period_end else None,
            },
        })


class InvoiceDetailView(APIView):
    """
    GET  /api/payments/invoice/<appointment_id>/
    Returns full invoice details for an appointment.

    PATCH /api/payments/invoice/<appointment_id>/
    Update payment details.
    Body: { "payment_status": "paid", "payment_type": "online", "payment_amount": 420.00 }
    """
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Viewing: any staff. Editing an invoice: admin / reception only.
        if self.request.method in ('PATCH', 'PUT'):
            return [IsAdminOrReception()]
        return [IsAuthenticated()]

    def get(self, request, appointment_id):
        from appointments.models import Appointment
        try:
            appt = Appointment.objects.select_related(
                'patient', 'treatment', 'staff', 'price_plan'
            ).get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        amount    = float(appt.payment_amount) if appt.payment_amount else 0.0
        tax_rate  = 0.07  # 7% VAT
        tax       = round(amount * tax_rate, 2)
        total     = round(amount + tax, 2)

        return Response({
            'invoice_id':      f"#AURA-{appt.date_time.year if appt.date_time else '2026'}-{appt.id}",
            'appointment_id':  appt.id,
            'date':            appt.date_time.strftime('%B %d, %Y') if appt.date_time else '',
            'patient': {
                'name':       appt.patient.name if appt.patient else '',
                'patient_id': appt.patient.patient_id if appt.patient else '',
                'phone':      appt.patient.phone if appt.patient else '',
                'email':      appt.patient.email if appt.patient else '',
            },
            'therapist': {
                'name':           appt.staff.username if appt.staff else '',
                'specialist_area': appt.staff.specialist_area if appt.staff else '',
            },
            'service': {
                'name':      appt.treatment.name if appt.treatment else '',
                'category':  appt.treatment.category if appt.treatment else '',
                'duration':  appt.duration,
                'amount':    f"€{amount:.2f}",
            },
            'pricing': {
                'subtotal':     f"€{amount:.2f}",
                'tax_rate':     '7%',
                'tax_amount':   f"€{tax:.2f}",
                'total_amount': f"€{total:.2f}",
            },
            'payment': {
                'status':       appt.payment_status,
                'type':         appt.payment_type,
                'amount':       f"€{amount:.2f}",
                'total':        f"€{total:.2f}",
            },
        })

    def patch(self, request, appointment_id):
        from appointments.models import Appointment
        try:
            appt = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        payment_status = request.data.get('payment_status')
        payment_type   = request.data.get('payment_type')
        payment_amount = request.data.get('payment_amount')

        if payment_status in ['pending', 'paid', 'refunded']:
            appt.payment_status = payment_status
        if payment_type in ['online', 'cash']:
            appt.payment_type = payment_type
        if payment_amount is not None:
            appt.payment_amount = payment_amount

        appt.save()

        return Response({
            'message':        'Payment details updated.',
            'appointment_id': appt.id,
            'payment_status': appt.payment_status,
            'payment_type':   appt.payment_type,
            'payment_amount': str(appt.payment_amount) if appt.payment_amount else None,
        })


class MarkAsPaidView(APIView):
    """
    POST /api/payments/mark-paid/
    Body: { "appointment_id": 42 }
    Manually mark appointment as paid (cash payment)
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request):
        from appointments.models import Appointment

        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response({'error': 'appointment_id is required.'}, status=400)

        try:
            appt = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        appt.payment_status = 'paid'
        appt.payment_type   = 'cash'
        appt.save()

        return Response({
            'success':        True,
            'message':        'Appointment marked as paid.',
            'appointment_id': appt.id,
            'payment_status': appt.payment_status,
        })



@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    POST /api/payments/webhook/
    """
    permission_classes     = []
    authentication_classes = []

    def post(self, request):
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        payload        = request.body
        sig_header     = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)

        from appointments.models import Appointment

        if event['type'] == 'checkout.session.completed':
            session        = event['data']['object']
            appt_id        = session.get('metadata', {}).get('appointment_id')
            payment_intent = session.get('payment_intent')
            if appt_id:
                try:
                    appt = Appointment.objects.get(id=appt_id)
                    appt.payment_status = 'paid'
                    appt.payment_type   = 'online'
                    # Store payment_intent_id in notes field for refund lookup
                    if payment_intent:
                        appt.notes = f"stripe_pi:{payment_intent}"
                    appt.save()
                except Appointment.DoesNotExist:
                    pass

        elif event['type'] == 'payment_intent.succeeded':
            appt_id = event['data']['object']['metadata'].get('appointment_id')
            if appt_id:
                try:
                    appt = Appointment.objects.get(id=appt_id)
                    appt.payment_status = 'paid'
                    appt.save()
                except Appointment.DoesNotExist:
                    pass

        elif event['type'] == 'payment_intent.payment_failed':
            appt_id = event['data']['object']['metadata'].get('appointment_id')
            if appt_id:
                try:
                    appt = Appointment.objects.get(id=appt_id)
                    appt.payment_status = 'pending'
                    appt.save()
                except Appointment.DoesNotExist:
                    pass

        return HttpResponse(status=200)