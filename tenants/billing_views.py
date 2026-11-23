"""Clinic billing endpoints (/api/billing/...) and the Stripe billing webhook."""
import datetime
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


def _resolve_plan(request, clinic):
    """Plan from ?plan_id (active plans only), else the clinic's plan, else the default. → (plan, error)."""
    plan = clinic.plan
    raw_plan = request.data.get('plan_id')
    if raw_plan not in (None, ''):
        plan = Plan.objects.filter(pk=raw_plan, is_active=True).first() if str(raw_plan).isdigit() else None
        if plan is None:
            return None, Response({'plan_id': 'Plan not found.'}, status=400)
    plan = plan or b.default_plan()
    if plan is None or not plan.stripe_price_id:
        return None, Response({'plan_id': 'This plan is not set up for billing yet (no Stripe price).',
                               'code': 'plan_not_billable'}, status=400)
    return plan, None


def _ensure_customer(stripe, clinic, user):
    if not clinic.stripe_customer_id:
        customer = stripe.Customer.create(
            name=clinic.name, email=user.email,
            metadata={'clinic_id': str(clinic.id)},
            idempotency_key=f'clinic-{clinic.id}-customer',
        )
        clinic.stripe_customer_id = customer['id']
        Clinic.objects.filter(pk=clinic.pk).update(stripe_customer_id=clinic.stripe_customer_id)
    return clinic.stripe_customer_id


def _has_live_subscription(clinic):
    return bool(clinic.stripe_subscription_id) and clinic.subscription_status in ('trialing', 'active', 'past_due')


def _allowed_return_url(url):
    """Return URLs must point at our own frontend (CORS_ALLOWED_ORIGINS / BILLING_RETURN_ORIGINS) or localhost."""
    from urllib.parse import urlparse
    from django.conf import settings
    try:
        u = urlparse(str(url or ''))
    except ValueError:
        return False
    if u.scheme not in ('http', 'https') or not u.hostname:
        return False
    if u.hostname in ('localhost', '127.0.0.1'):
        return True
    origins = list(getattr(settings, 'CORS_ALLOWED_ORIGINS', []) or [])
    origins += [o.strip() for o in os.environ.get('BILLING_RETURN_ORIGINS', '').split(',') if o.strip()]
    if not origins:
        return u.scheme == 'https'
    return f'{u.scheme}://{u.netloc}'.lower() in {o.rstrip('/').lower() for o in origins}


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
        plan, error = _resolve_plan(request, clinic)
        if error:
            return error

        now = timezone.now()
        action_type = client_secret = None
        try:
            # 1. Customer + card
            _ensure_customer(stripe, clinic, request.user)
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


class CheckoutSessionView(APIView):
    """
    POST /api/billing/checkout-session/   (clinic admin)  — for web: redirect to Stripe's hosted page
    {"success_url": "https://app…/billing?checkout=success", "cancel_url": "https://app…/billing?checkout=cancel", "plan_id": 1?}
    → {"url": "https://checkout.stripe.com/…", "session_id": "cs_…", "expires_at": "…"}
    A trialing clinic keeps its remaining trial (first charge at trial_end); otherwise it is charged at checkout.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        stripe = b.stripe_client()
        if stripe is None:
            return Response({'error': 'Billing is not configured on the server.', 'code': 'billing_not_configured'}, status=503)
        clinic = _clinic_of(request)
        errors = {}
        for field in ('success_url', 'cancel_url'):
            if not request.data.get(field):
                errors[field] = 'This field is required.'
            elif not _allowed_return_url(request.data.get(field)):
                errors[field] = 'Must be a URL of the Aura web app (an allowed origin).'
        if errors:
            return Response(errors, status=400)
        if _has_live_subscription(clinic):
            return Response({'error': 'This clinic already has a subscription. Use the billing portal to change the card or plan.',
                             'code': 'subscription_exists'}, status=409)
        plan, error = _resolve_plan(request, clinic)
        if error:
            return error

        success_url = str(request.data['success_url'])
        if '{CHECKOUT_SESSION_ID}' not in success_url:
            success_url += ('&' if '?' in success_url else '?') + 'session_id={CHECKOUT_SESSION_ID}'
        now = timezone.now()
        subscription_data = {'metadata': {'clinic_id': str(clinic.id), 'plan_id': str(plan.id)}}
        if clinic.subscription_status == 'trialing' and clinic.trial_end and clinic.trial_end > now:
            # Stripe needs a trial end at least 48 hours away; a trial with less left is stretched to that.
            earliest = now + datetime.timedelta(hours=48, minutes=10)
            subscription_data['trial_end'] = int(max(clinic.trial_end, earliest).timestamp())
        try:
            _ensure_customer(stripe, clinic, request.user)
            session = stripe.checkout.Session.create(
                mode='subscription',
                customer=clinic.stripe_customer_id,
                client_reference_id=str(clinic.id),
                line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
                payment_method_collection='always',
                subscription_data=subscription_data,
                metadata={'clinic_id': str(clinic.id), 'plan_id': str(plan.id)},
                success_url=success_url,
                cancel_url=str(request.data['cancel_url']),
            )
        except stripe.error.StripeError as e:
            log.warning('Stripe checkout error for clinic %s: %s', clinic.id, e)
            return Response({'error': 'Payment provider error. Please try again.', 'code': 'stripe_error'}, status=502)
        return Response({'url': b._get(session, 'url'), 'session_id': b._get(session, 'id'),
                         'expires_at': b._ts(b._get(session, 'expires_at'))})


class CheckoutConfirmView(APIView):
    """
    POST /api/billing/checkout-session/confirm/   {"session_id": "cs_…"}   (clinic admin)
    Call after Stripe redirects back to success_url: applies the subscription straight away
    (the webhook does the same a moment later). Returns the billing status + checkout_status.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        stripe = b.stripe_client()
        if stripe is None:
            return Response({'error': 'Billing is not configured on the server.', 'code': 'billing_not_configured'}, status=503)
        session_id = str(request.data.get('session_id', '') or '').strip()
        if not session_id.startswith('cs_'):
            return Response({'session_id': 'A Checkout Session id (cs_…) is required.'}, status=400)
        clinic = _clinic_of(request)
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.InvalidRequestError:
            return Response({'error': 'Checkout session not found.'}, status=404)
        except stripe.error.StripeError:
            return Response({'error': 'Payment provider error. Please try again.', 'code': 'stripe_error'}, status=502)
        owner = b._get(session, 'client_reference_id') or b._get(b._get(session, 'metadata', {}) or {}, 'clinic_id')
        if str(owner) != str(clinic.id):
            return Response({'error': 'Checkout session not found.'}, status=404)
        checkout_status = b._get(session, 'status')          # open | complete | expired
        if checkout_status == 'complete':
            try:
                with transaction.atomic():
                    clinic = Clinic.objects.select_for_update(of=('self',)).select_related('plan').get(pk=clinic.pk)
                    b.apply_checkout_session(clinic, session, stripe)
                    clinic.save()
            except stripe.error.StripeError:
                return Response({'error': 'Payment provider error. Please try again.', 'code': 'stripe_error'}, status=502)
        data = b.billing_payload(clinic)
        data['checkout_status'] = checkout_status
        return Response(data)


class PortalSessionView(APIView):
    """
    POST /api/billing/portal-session/   {"return_url": "https://app…/billing"}   (clinic admin)
    → {"url": "https://billing.stripe.com/…"}  Stripe's hosted page to update the card, see invoices or cancel.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        stripe = b.stripe_client()
        if stripe is None:
            return Response({'error': 'Billing is not configured on the server.', 'code': 'billing_not_configured'}, status=503)
        return_url = request.data.get('return_url')
        if not return_url or not _allowed_return_url(return_url):
            return Response({'return_url': 'Must be a URL of the Aura web app (an allowed origin).'}, status=400)
        clinic = _clinic_of(request)
        if not clinic.stripe_customer_id:
            return Response({'error': 'No billing account yet. Start a subscription first.', 'code': 'no_billing_account'}, status=400)
        try:
            session = stripe.billing_portal.Session.create(customer=clinic.stripe_customer_id, return_url=str(return_url))
        except stripe.error.StripeError as e:
            log.warning('Stripe portal error for clinic %s: %s', clinic.id, e)
            return Response({'error': 'The billing portal is not available right now.', 'code': 'stripe_error'}, status=502)
        return Response({'url': b._get(session, 'url')})


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
    customer.subscription.updated   → keeps next billing date / trial end / cancel_at_period_end in sync
    checkout.session.completed      → subscription started from Stripe Checkout (web), or — mode=payment —
                                      a patient's appointment payment (recorded on the invoice)
    payment_intent.succeeded        → a patient's appointment payment from the mobile app
    customer.updated                → card changed in the billing portal
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
                  'customer.subscription.deleted', 'customer.subscription.updated',
                  'checkout.session.completed', 'customer.updated', 'payment_intent.succeeded')


def handle_event(event):
    etype = b._get(event, 'type')
    if etype not in HANDLED_EVENTS:
        return None
    obj = b._get(b._get(event, 'data', {}), 'object', {})
    from payments.stripe_sync import plain
    obj = plain(obj) or {}
    # Patients paying for appointments (not the clinic's subscription): forwarded to the invoice
    # code, so this one webhook endpoint is enough for both. Recording there is idempotent.
    meta = b._get(obj, 'metadata', {}) or {}
    if (etype == 'checkout.session.completed' and b._get(obj, 'mode') == 'payment') or \
            (etype == 'payment_intent.succeeded' and (meta.get('appointment_id') or meta.get('invoice_id'))):
        from payments.stripe_sync import apply_checkout_session, apply_payment_intent
        (apply_checkout_session if etype == 'checkout.session.completed' else apply_payment_intent)(obj)
        return None
    if etype == 'payment_intent.succeeded':
        return None
    created = b._ts(b._get(event, 'created')) or timezone.now()
    with transaction.atomic():
        if etype == 'customer.updated':
            clinic = Clinic.objects.select_for_update().filter(stripe_customer_id=b._get(obj, 'id')).first()
        elif etype == 'checkout.session.completed':
            ref = b._get(obj, 'client_reference_id')
            clinic = (Clinic.objects.select_for_update().filter(pk=int(ref)).first()
                      if ref and str(ref).isdigit() else _clinic_for(obj))
        else:
            clinic = _clinic_for(obj)
        if clinic is None:
            return None
        if clinic.last_billing_event_at and created < clinic.last_billing_event_at and etype not in ('customer.subscription.deleted', 'checkout.session.completed', 'customer.updated'):
            return clinic   # older than what we've already applied

        if etype == 'checkout.session.completed':
            if b._get(obj, 'mode') != 'subscription':
                return None
            stripe = b.stripe_client()
            if stripe is None:
                return clinic
            b.apply_checkout_session(clinic, obj, stripe)
        elif etype == 'customer.updated':
            pm = b._get(b._get(obj, 'invoice_settings', {}) or {}, 'default_payment_method')
            stripe = b.stripe_client()
            if pm and stripe is not None:
                b.apply_default_card(clinic, stripe, pm)
            clinic.save()
            return clinic          # not a status change: don't move last_billing_event_at
        elif etype.startswith('invoice.'):
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
            clinic.cancel_at_period_end = False
        elif etype == 'customer.subscription.updated':
            if clinic.stripe_subscription_id and b._get(obj, 'id') != clinic.stripe_subscription_id:
                return clinic
            clinic.current_period_end = b.period_end_of(obj) or clinic.current_period_end
            clinic.cancel_at_period_end = bool(b._get(obj, 'cancel_at_period_end', False))
            if b._get(obj, 'status') == 'trialing':
                clinic.trial_end = b._ts(b._get(obj, 'trial_end')) or clinic.trial_end

        clinic.last_billing_event_at = created
        clinic.save()
        return clinic
