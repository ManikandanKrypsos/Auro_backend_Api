import stripe
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils.decorators import method_decorator

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')


class CreatePaymentIntentView(APIView):
    """
    POST /api/payments/create-intent/
    Body: { "appointment_id": 42 }
    Returns client_secret for Flutter Stripe SDK
    """
    permission_classes = [IsAuthenticated]

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
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
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
                'amount_display':    f"${float(amount):.2f}",
                'currency':          'usd',
                'appointment_id':    appt.id,
                'patient':           appt.patient.name if appt.patient else '',
                'treatment':         appt.treatment.name if appt.treatment else '',
            })

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=400)


class ConfirmPaymentView(APIView):
    """
    POST /api/payments/confirm/
    Body: { "appointment_id": 42, "payment_intent_id": "pi_xxx" }
    Call this after Flutter confirms payment with Stripe SDK
    """
    permission_classes = [IsAuthenticated]

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
                    'amount_paid':    f"${float(appt.payment_amount):.2f}" if appt.payment_amount else '',
                })
            else:
                return Response({'success': False, 'message': f"Payment not completed. Status: {intent.status}"}, status=400)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=400)


class RefundPaymentView(APIView):
    """
    POST /api/payments/refund/
    Body: { "appointment_id": 42 }
    Refunds payment for a cancelled appointment
    """
    permission_classes = [IsAuthenticated]

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

        try:
            intents     = stripe.PaymentIntent.list(limit=100)
            target      = None
            for intent in intents.data:
                if intent.metadata.get('appointment_id') == str(appt.id):
                    target = intent
                    break

            if not target:
                return Response({'error': 'Payment record not found in Stripe.'}, status=404)

            refund = stripe.Refund.create(payment_intent=target.id)

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
            return Response({'error': str(e)}, status=400)


class PaymentStatusView(APIView):
    """
    GET /api/payments/status/<appointment_id>/
    Get payment status for an appointment
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
            'amount_display': f"${float(appt.payment_amount):.2f}" if appt.payment_amount else None,
        })


class PaymentListView(APIView):
    """
    GET /api/payments/
    GET /api/payments/?status=paid
    GET /api/payments/?status=pending
    GET /api/payments/?search=john
    GET /api/payments/?sort=date_desc   (default)
    GET /api/payments/?sort=date_asc

    Returns all appointments with payment info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from appointments.models import Appointment

        status = request.query_params.get('status', '').strip().lower()
        search = request.query_params.get('search', '').strip()
        sort   = request.query_params.get('sort', 'date_desc').strip()

        qs = Appointment.objects.select_related(
            'patient', 'treatment', 'staff'
        ).exclude(payment_amount__isnull=True).exclude(status='cancelled')

        if status in ['paid', 'pending', 'refunded']:
            qs = qs.filter(payment_status=status)

        if search:
            qs = qs.filter(patient__name__icontains=search)

        if sort == 'date_asc':
            qs = qs.order_by('date_time')
        else:
            qs = qs.order_by('-date_time')

        result = []
        for appt in qs:
            result.append({
                'appointment_id':  appt.id,
                'patient_name':    appt.patient.name if appt.patient else '',
                'treatment_name':  appt.treatment.name if appt.treatment else '',
                'date':            appt.date_time.strftime('%b %d, %Y') if appt.date_time else '',
                'amount':          f"${float(appt.payment_amount):.2f}" if appt.payment_amount else '$0.00',
                'payment_status':  appt.payment_status,
                'payment_type':    appt.payment_type,
            })

        # Stats for tabs
        all_qs      = Appointment.objects.exclude(payment_amount__isnull=True).exclude(status='cancelled')
        total_paid  = sum(float(a.payment_amount) for a in all_qs.filter(payment_status='paid') if a.payment_amount)
        total_pending = sum(float(a.payment_amount) for a in all_qs.filter(payment_status='pending') if a.payment_amount)

        return Response({
            'payments': result,
            'stats': {
                'total':         all_qs.count(),
                'paid_count':    all_qs.filter(payment_status='paid').count(),
                'pending_count': all_qs.filter(payment_status='pending').count(),
                'total_paid':    f"${total_paid:.2f}",
                'total_pending': f"${total_pending:.2f}",
            }
        })
    """
    GET /api/payments/status/<appointment_id>/
    Get payment status for an appointment
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
            'amount_display': f"${float(appt.payment_amount):.2f}" if appt.payment_amount else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    POST /api/payments/webhook/
    Add this URL in Stripe Dashboard → Webhooks
    Events: payment_intent.succeeded, payment_intent.payment_failed
    """
    permission_classes    = []
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

        if event['type'] == 'payment_intent.succeeded':
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