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


def _amount_due(appt):
    """(amount, None) = the invoice balance to charge, or (None, error Response)."""
    from .invoicing import invoice_for_appointment
    invoice = invoice_for_appointment(appt)
    if invoice.status == 'void':
        return None, Response({'error': 'This appointment was cancelled; there is nothing to pay.'}, status=400)
    if invoice.balance_due <= 0:
        return None, Response({'error': 'This appointment is already paid.' if invoice.total > 0
                               else 'No price set for this appointment.'}, status=400)
    return invoice.balance_due, None


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

        # Charge what is still due on the appointment's invoice (supports partly-paid invoices)
        amount, error_response = _amount_due(appt)
        if error_response:
            return error_response
        from .invoicing import invoice_for_appointment
        invoice_id = invoice_for_appointment(appt).id

        # Where Stripe sends the patient back. The app may pass its own URLs (same rules as the
        # subscription checkout); {CHECKOUT_SESSION_ID} is always added so the app can verify.
        from tenants.billing_views import _allowed_return_url
        default_base = 'https://krypsos-auro.onrender.com/#/'
        success_url = request.data.get('success_url') or f'{default_base}paymentSuccessScreen?appointment_id={appt.id}'
        cancel_url = request.data.get('cancel_url') or f'{default_base}paymentCancelScreen?appointment_id={appt.id}'
        for field, url in (('success_url', success_url), ('cancel_url', cancel_url)):
            if request.data.get(field) and not _allowed_return_url(url):
                return Response({field: 'Must be a URL of the Aura web app (an allowed origin).'}, status=400)
        if '{CHECKOUT_SESSION_ID}' not in success_url:
            success_url += ('&' if '?' in success_url else '?') + 'session_id={CHECKOUT_SESSION_ID}'

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
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(appt.id),
                payment_intent_data={'metadata': {'appointment_id': str(appt.id), 'invoice_id': str(invoice_id)}},
                metadata={
                    'appointment_id': str(appt.id),
                    'invoice_id':     str(invoice_id),
                    'patient_name':   appt.patient.name if appt.patient else '',
                    'treatment_name': appt.treatment.name if appt.treatment else '',
                },
            )

            # The price stays on the invoice; mark the appointment as paying online
            type(appt).objects.filter(pk=appt.pk).update(payment_type='online')

            from .models import Invoice
            Invoice._base_manager.filter(pk=invoice_id).update(stripe_checkout_session_id=session.id)
            return Response({
                'checkout_url': session.url,
                'session_id':   session.id,
                'invoice_id':   invoice_id,
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

        # Charge what is still due on the appointment's invoice (supports partly-paid invoices)
        amount, error_response = _amount_due(appt)
        if error_response:
            return error_response

        amount_cents = int(float(amount) * 100)

        try:
            from .invoicing import invoice_for_appointment
            invoice_id = invoice_for_appointment(appt).id
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='eur',
                metadata={
                    'appointment_id': str(appt.id),
                    'invoice_id':     str(invoice_id),
                    'patient_name':   appt.patient.name if appt.patient else '',
                    'treatment_name': appt.treatment.name if appt.treatment else '',
                },
                description=f"Aura Clinic — {appt.treatment.name if appt.treatment else 'Treatment'} for {appt.patient.name if appt.patient else 'Patient'}",
            )

            # The price stays on the invoice; mark the appointment as paying online
            type(appt).objects.filter(pk=appt.pk).update(payment_type='online')

            from .models import Invoice
            Invoice._base_manager.filter(pk=invoice_id).update(stripe_payment_intent_id=intent.id)
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
            from .stripe_sync import plain
            meta = (plain(intent) or {}).get('metadata') or {}
            if str(meta.get('appointment_id', '')) != str(appt.id):
                return Response({'error': 'This payment does not belong to this appointment.'}, status=400)
            if intent.status == 'succeeded':
                from .stripe_sync import apply_payment_intent
                apply_payment_intent(intent)          # idempotent: safe if the webhook already did it
                appt.refresh_from_db()
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
            from .models import Payment
            rec = (Payment.objects.filter(invoice__appointment=appt, kind='payment', method='online',
                                          reference__startswith='pi_').order_by('-paid_at').first())
            if rec:
                payment_intent_id = rec.reference
            if not payment_intent_id and appt.notes and appt.notes.startswith('stripe_pi:'):
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


def _invoice_bits(appt):
    i = getattr(appt, 'invoice', None)
    if i is None:
        return {'invoice_id': None, 'invoice_number': None, 'invoice_status': None,
                'amount_paid': 0.0, 'balance_due': float(appt.payment_amount or 0)}
    return {'invoice_id': i.id, 'invoice_number': i.invoice_number, 'invoice_status': i.status,
            'amount_paid': round(float(i.amount_paid), 2), 'balance_due': round(float(i.balance_due), 2)}


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
    Money: total_paid = payments received in the period (minus refunds); total_pending =
    balance still due on invoices issued in the period (see payments/metrics.py).

    POST /api/payments/  — record a payment against an invoice (cash / card / transfer / …)
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request):
        from .invoice_views import record_payment
        return record_payment(request)

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
        qs = in_period(base, period_start, period_end).select_related('patient', 'treatment', 'staff', 'invoice')
        if status in ['paid', 'pending', 'refunded']:
            qs = qs.filter(payment_status=status)
        elif status == 'partially_paid':
            qs = qs.filter(invoice__status='partially_paid')
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
                **_invoice_bits(appt),
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
            prev_start, prev_end = period_start, som - datetime.timedelta(days=1)
        cur, prev = _payment_totals(cur_qs), _payment_totals(prev_qs)
        from .metrics import outstanding_total, payments_between, received_total
        cur_from, cur_to = period_start, period_end
        if not (period_start and period_end):
            cur_to = period_end
        cur['total_paid'] = received_total(cur_from, cur_to, staff_id)
        cur['total_pending'] = outstanding_total(cur_from, cur_to, staff_id)
        prev['total_paid'] = received_total(prev_start, prev_end, staff_id)
        prev['total_pending'] = outstanding_total(prev_start, prev_end, staff_id)

        billed = cur['total_paid'] + cur['total_pending']
        paid_pct, pending_pct = _pcts([cur['total_paid'], cur['total_pending']])

        # Methods: payments received in the period (refunds not counted), share of count.
        # Online (Stripe) is a card payment for this breakdown.
        method_counts = {m: 0 for m in PAYMENT_METHODS}
        method_amount = {m: 0.0 for m in PAYMENT_METHODS}
        for method, amount in payments_between(cur_from, cur_to, staff_id).filter(kind='payment') \
                .values_list('method', 'amount'):
            m = 'card' if method == 'online' else (method if method in method_counts else 'other')
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

        # Backed by the real invoice now (prices include tax). Same response shape as before,
        # plus invoice_number / amount_paid / balance_due / lines.
        from .invoicing import invoice_for_appointment
        from .invoice_views import serialize_line
        invoice = invoice_for_appointment(appt, request.user)
        total    = float(invoice.total)
        tax      = float(invoice.tax_amount)
        amount   = float(invoice.subtotal)
        lines    = [serialize_line(l) for l in invoice.lines.all()]
        rates    = sorted({l['tax_rate'] for l in lines})
        rate_txt = ', '.join(f"{r:g}%" for r in rates) or '0%'

        return Response({
            'invoice_id':      invoice.invoice_number,
            'invoice_db_id':   invoice.id,
            'invoice_number':  invoice.invoice_number,
            'invoice_status':  invoice.status,
            'due_date':        invoice.due_date,
            'amount_paid':     round(float(invoice.amount_paid), 2),
            'balance_due':     round(float(invoice.balance_due), 2),
            'lines':           lines,
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
                'amount':    f"€{total:.2f}",
            },
            'pricing': {
                'subtotal':     f"€{amount:.2f}",
                'tax_rate':     rate_txt,
                'tax_amount':   f"€{tax:.2f}",
                'total_amount': f"€{total:.2f}",
                'prices_include_tax': True,
            },
            'payment': {
                'status':       appt.payment_status,
                'type':         appt.payment_type,
                'amount':       f"€{float(invoice.amount_paid):.2f}",
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

        # Appointment / invoice payments. Recording is idempotent (see stripe_sync), so this endpoint and
        # the billing webhook (which also forwards these events) can both receive them safely.
        from .stripe_sync import apply_checkout_session, apply_payment_intent
        from .stripe_sync import plain
        event = plain(event)
        obj = event['data']['object']
        try:
            if event['type'] == 'checkout.session.completed' and obj.get('mode') == 'payment':
                apply_checkout_session(obj)
            elif event['type'] == 'payment_intent.succeeded':
                apply_payment_intent(obj)
            # payment_intent.payment_failed: nothing to record — the invoice simply stays unpaid
        except Exception:
            logger.exception('Stripe webhook %s failed', event.get('id'))
            return HttpResponse(status=500)       # Stripe retries
        return HttpResponse(status=200)


class ReconcileStripeView(APIView):
    """
    POST /api/payments/reconcile-session/
    {"session_id": "cs_…"}  or  {"payment_intent_id": "pi_…"}  or  {"appointment_id": 42}  or  {"invoice_id": 51}
    Asks Stripe directly whether the payment went through and records it if it did — for when a
    webhook was missed or is late. Safe to call any number of times (never records twice).
    With appointment_id / invoice_id, the last checkout / payment started for that invoice is checked.
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request):
        from .invoice_views import serialize_invoice, serialize_payment, _get_invoice
        from .models import Invoice
        from .stripe_sync import apply_checkout_session, apply_payment_intent, invoice_for, plain
        from utils.api_errors import error, validation_error
        d = request.data
        session_id = str(d.get('session_id', '') or '').strip()
        pi_id = str(d.get('payment_intent_id', '') or '').strip()
        if not session_id and not pi_id:
            raw_appt, raw_inv = str(d.get('appointment_id', '') or ''), str(d.get('invoice_id', '') or '')
            if not raw_appt and not raw_inv:
                return validation_error({'session_id': 'Send session_id, payment_intent_id, appointment_id or invoice_id.'})
            if (raw_appt and not raw_appt.isdigit()) or (raw_inv and not raw_inv.isdigit()):
                return validation_error({'appointment_id' if raw_appt else 'invoice_id': 'Must be an id.'})
            from appointments.models import Appointment
            if raw_appt and not Appointment.objects.filter(pk=int(raw_appt)).exists():
                return error(404, 'appointment_not_found', 'Appointment not found.')
            if raw_inv and not Invoice.objects.filter(pk=int(raw_inv)).exists():
                return error(404, 'invoice_not_found', 'Invoice not found.')
            invoice = invoice_for(int(raw_appt) if raw_appt else None, int(raw_inv) if raw_inv else None)
            session_id = invoice.stripe_checkout_session_id
            pi_id = invoice.stripe_payment_intent_id
            if not session_id and not pi_id:
                return error(404, 'no_stripe_payment', 'No Stripe payment has been started for this invoice.')
        elif session_id and not session_id.startswith('cs_'):
            return validation_error({'session_id': 'A Checkout Session id (cs_…) is required.'})
        elif pi_id and not pi_id.startswith('pi_'):
            return validation_error({'payment_intent_id': 'A PaymentIntent id (pi_…) is required.'})

        try:
            if session_id:
                obj = plain(stripe.checkout.Session.retrieve(session_id))
                stripe_status = obj.get('payment_status')
            else:
                obj = plain(stripe.PaymentIntent.retrieve(pi_id))
                stripe_status = obj.get('status')
        except stripe.error.InvalidRequestError:
            return error(404, 'stripe_not_found', 'Stripe has no payment with that id.')
        except stripe.error.StripeError as e:
            logger.warning('Stripe error: %s', e)
            return error(502, 'stripe_error', 'Could not reach Stripe. Please try again.')

        meta = obj.get('metadata') or {}
        # only for this clinic's invoices: the scoped lookups return nothing for another clinic's
        from appointments.models import Appointment
        appt_ok = meta.get('appointment_id') and Appointment.objects.filter(pk=meta['appointment_id']).exists()
        inv_ok = meta.get('invoice_id') and Invoice.objects.filter(pk=meta['invoice_id']).exists()
        if not appt_ok and not inv_ok:
            return error(404, 'stripe_not_found', 'That Stripe payment is not for this clinic.')

        invoice, payment, outcome = (apply_checkout_session(obj) if session_id else apply_payment_intent(obj))
        if invoice is None:
            return error(404, 'invoice_not_found', 'Invoice not found for this Stripe payment.')
        paid = outcome in ('recorded', 'already_recorded', 'already_paid')
        return Response({
            'stripe_status':  stripe_status,          # paid / unpaid / no_payment_required · succeeded / processing / …
            'paid':           paid,
            'outcome':        outcome if paid else 'not_paid',
            'payment':        serialize_payment(payment) if payment else None,
            'invoice':        serialize_invoice(_get_invoice(invoice.pk)),
        })
