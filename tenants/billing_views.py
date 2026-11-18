"""Clinic billing endpoints (/api/billing/...) and the Stripe billing webhook."""
import logging
import os

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from . import billing as b
from .models import Clinic, Plan

log = logging.getLogger(__name__)


def _clinic_of(request):
    return Clinic.objects.select_related('plan').get(pk=request.user.clinic_id)


class PlanListView(APIView):
    """GET /api/billing/plans/ — plans a clinic can choose (public: also used on the sign-up screen)."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response([b.serialize_plan(p) for p in Plan.objects.filter(is_active=True)])


class BillingStatusView(APIView):
    """GET /api/billing/status/ — plan, status, trial / next billing date, card. Any clinic user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clinic = b.refresh_trial_status(_clinic_of(request))
        data = b.billing_payload(clinic)
        data['stripe_publishable_key'] = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
        return Response(data)


def _client_secret_needed(sub, invoice=None):
    """If the card needs 3-D Secure, returns (type, client_secret) for stripe.js to confirm."""
    inv = invoice if invoice is not None else b._get(sub, 'latest_invoice')
    pi = b._get(inv, 'payment_intent') if inv is not None and not isinstance(inv, str) else None
    if pi is not None and not isinstance(pi, str) and b._get(pi, 'status') in ('requires_action', 'requires_confirmation'):
        return 'payment', b._get(pi, 'client_secret')
    si = b._get(sub, 'pending_setup_intent') if sub is not None else None
    if si is not None and not isinstance(si, str) and b._get(si, 'status') in ('requires_action', 'requires_confirmation'):
        return 'setup', b._get(si, 'client_secret')
    return None, None


class AddCardView(APIView):
    """
    POST /api/billing/add-card/   (clinic admin)
    {"payment_method_id": "pm_…", "plan_id": 1?}

    Saves the card (created on the frontend with Stripe.js) and starts the subscription — or, if the
    clinic already has one, makes this the card for it and retries any unpaid invoice.
    During a trial, the subscription keeps the remaining trial days (first charge at trial_end).
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        stripe = b.stripe_client()
        if stripe is None:
            return Response({'error': 'Billing is not configured on the server.', 'code': 'billing_not_configured'}, status=503)

        pm_id = str(request.data.get('payment_method_id', '') or '').strip()
        if not pm_id.startswith('pm_'):
            return Response({'payment_method_id': 'A Stripe PaymentMethod id (pm_…) is required.'}, status=400)

        clinic = _clinic_of(request)
        plan = clinic.plan
        raw_plan = request.data.get('plan_id')
        if raw_plan not in (None, ''):
            plan = Plan.objects.filter(pk=raw_plan, is_active=True).first() if str(raw_plan).isdigit() else None
            if plan is None:
                return Response({'plan_id': 'Plan not found.'}, status=400)
        plan = plan or b.default_plan()
        if plan is None or not plan.stripe_price_id:
            return Response({'plan_id': 'This plan is not set up for billing yet (no Stripe price).'}, status=400)

        now = timezone.now()
        action_type = client_secret = None
        try:
            # 1. Customer + card
            if not clinic.stripe_customer_id:
                customer = stripe.Customer.create(
                    name=clinic.name, email=request.user.email,
                    metadata={'clinic_id': str(clinic.id)},
                    idempotency_key=f'clinic-{clinic.id}-customer',
                )
                clinic.stripe_customer_id = customer['id']
                Clinic.objects.filter(pk=clinic.pk).update(stripe_customer_id=clinic.stripe_customer_id)
            pm = stripe.PaymentMethod.attach(pm_id, customer=clinic.stripe_customer_id)
            stripe.Customer.modify(clinic.stripe_customer_id, invoice_settings={'default_payment_method': pm_id})
            b.apply_card(clinic, pm)

            # 2. Existing subscription → switch card (and plan), retry unpaid invoice
            sub = None
            if clinic.stripe_subscription_id:
                existing = stripe.Subscription.retrieve(clinic.stripe_subscription_id)
                if b._get(existing, 'status') not in ('canceled', 'incomplete_expired'):
                    params = {'default_payment_method': pm_id}
                    items = b._get(b._get(existing, 'items', {}), 'data', []) or []
                    if items and b._get(b._get(items[0], 'price', {}), 'id') != plan.stripe_price_id:
                        params['items'] = [{'id': b._get(items[0], 'id'), 'price': plan.stripe_price_id}]
                    sub = stripe.Subscription.modify(clinic.stripe_subscription_id, **params)
                    invoice_id = b._get(existing, 'latest_invoice')
                    if b._get(existing, 'status') in ('past_due', 'unpaid', 'incomplete') and invoice_id:
                        invoice_id = invoice_id if isinstance(invoice_id, str) else b._get(invoice_id, 'id')
                        try:
                            stripe.Invoice.pay(invoice_id, payment_method=pm_id)
                        except stripe.error.CardError:
                            pass   # handled below: either needs 3-D Secure or the card was declined
                        invoice = stripe.Invoice.retrieve(invoice_id, expand=['payment_intent'])
                        action_type, client_secret = _client_secret_needed(None, invoice)
                        if b._get(invoice, 'status') == 'paid':
                            b.set_active(clinic)
                        elif action_type is None:
                            return Response({'error': 'The card was declined. Please try another card.', 'code': 'card_declined'}, status=402)
                    sub = stripe.Subscription.retrieve(clinic.stripe_subscription_id)

            # 3. No live subscription → create one
            if sub is None:
                params = {
                    'customer': clinic.stripe_customer_id,
                    'items': [{'price': plan.stripe_price_id}],
                    'default_payment_method': pm_id,
                    'payment_behavior': 'allow_incomplete',
                    'metadata': {'clinic_id': str(clinic.id)},
                    'expand': ['latest_invoice.payment_intent', 'pending_setup_intent'],
                }
                if clinic.subscription_status == 'trialing' and clinic.trial_end and clinic.trial_end > now:
                    params['trial_end'] = int(clinic.trial_end.timestamp())
                sub = stripe.Subscription.create(**params)
                action_type, client_secret = _client_secret_needed(sub)
                if b._get(sub, 'status') == 'incomplete' and action_type is None:
                    stripe.Subscription.cancel(b._get(sub, 'id'))
                    return Response({'error': 'The card was declined. Please try another card.', 'code': 'card_declined'}, status=402)
        except stripe.error.CardError as e:
            return Response({'error': e.user_message or 'The card was declined.', 'code': 'card_declined'}, status=402)
        except stripe.error.StripeError as e:
            log.warning('Stripe error for clinic %s: %s', clinic.id, e)
            return Response({'error': 'Payment provider error. Please try again.', 'code': 'stripe_error'}, status=502)

        with transaction.atomic():
            clinic.plan = plan
            b.apply_subscription(clinic, sub, now)
            clinic.save()

        data = b.billing_payload(clinic)
        data.update({
            'requires_action': action_type is not None,
            'action_type':     action_type,       # "payment" → stripe.confirmCardPayment, "setup" → stripe.confirmCardSetup
            'client_secret':   client_secret,
        })
        return Response(data)


# ── Webhook ───────────────────────────────────────────────────────────────────

def _clinic_for(obj):
    customer = b._get(obj, 'customer')
    if customer and not isinstance(customer, str):
        customer = b._get(customer, 'id')
    clinic = Clinic.objects.select_for_update().filter(stripe_customer_id=customer).first() if customer else None
    if clinic is None:
        cid = b._get(b._get(obj, 'metadata', {}) or {}, 'clinic_id')
        if cid and str(cid).isdigit():
            clinic = Clinic.objects.select_for_update().filter(pk=int(cid)).first()
    return clinic


class BillingWebhookView(APIView):
    """
    POST /api/billing/webhook/   (Stripe → server; signature-checked)
    invoice.payment_succeeded       → active
    invoice.payment_failed          → past_due + grace period
    customer.subscription.deleted   → canceled (blocked)
    customer.subscription.updated   → keeps next billing date / trial end in sync
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        import stripe
        secret = os.environ.get('STRIPE_BILLING_WEBHOOK_SECRET') or os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        if not secret:
            return HttpResponse(status=503)
        try:
            event = stripe.Webhook.construct_event(request.body, request.META.get('HTTP_STRIPE_SIGNATURE', ''), secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)
        handle_event(event)
        return HttpResponse(status=200)


HANDLED_EVENTS = ('invoice.payment_succeeded', 'invoice.paid', 'invoice.payment_failed',
                  'customer.subscription.deleted', 'customer.subscription.updated')


def handle_event(event):
    etype = b._get(event, 'type')
    if etype not in HANDLED_EVENTS:
        return None
    obj = b._get(b._get(event, 'data', {}), 'object', {})
    created = b._ts(b._get(event, 'created')) or timezone.now()
    with transaction.atomic():
        clinic = _clinic_for(obj)
        if clinic is None:
            return None
        if clinic.last_billing_event_at and created < clinic.last_billing_event_at and etype != 'customer.subscription.deleted':
            return clinic   # older than what we've already applied

        if etype.startswith('invoice.'):
            sub_id = b._get(obj, 'subscription') or b._get(b._get(b._get(obj, 'parent', {}) or {}, 'subscription_details', {}) or {}, 'subscription')
            if sub_id and not isinstance(sub_id, str):
                sub_id = b._get(sub_id, 'id')
            if sub_id and clinic.stripe_subscription_id and sub_id != clinic.stripe_subscription_id \
                    and clinic.subscription_status != 'canceled':
                return clinic   # an old subscription of this customer
            if sub_id:
                clinic.stripe_subscription_id = sub_id
            if etype == 'invoice.payment_failed':
                b.set_past_due(clinic, created)
            else:
                lines = b._get(b._get(obj, 'lines', {}), 'data', []) or []
                end = b._get(b._get(lines[0], 'period', {}), 'end') if lines else None
                if (b._get(obj, 'amount_paid') or 0) == 0 and clinic.subscription_status == 'trialing':
                    pass   # the €0 invoice at the start of a trial — still trialing
                else:
                    b.set_active(clinic)
                    clinic.current_period_end = b._ts(end) or clinic.current_period_end
        elif etype == 'customer.subscription.deleted':
            if clinic.stripe_subscription_id and b._get(obj, 'id') != clinic.stripe_subscription_id:
                return clinic
            clinic.subscription_status = 'canceled'
            clinic.canceled_at = created
            clinic.grace_until = None
        elif etype == 'customer.subscription.updated':
            if clinic.stripe_subscription_id and b._get(obj, 'id') != clinic.stripe_subscription_id:
                return clinic
            clinic.current_period_end = b.period_end_of(obj) or clinic.current_period_end
            if b._get(obj, 'status') == 'trialing':
                clinic.trial_end = b._ts(b._get(obj, 'trial_end')) or clinic.trial_end

        clinic.last_billing_event_at = created
        clinic.save()
        return clinic
