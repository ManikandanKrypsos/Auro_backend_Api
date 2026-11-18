"""
Subscription billing for clinics (Stripe).

Stripe is the source of truth: the webhook mirrors invoice / subscription events onto the Clinic.
Access rules (checked on every clinic API call, see tenants.auth.check_clinic_user):

  trialing       → allowed until trial_end; after that, if no subscription exists → trial_expired (blocked)
  active         → allowed
  past_due       → allowed during the grace period (warning only); blocked after grace_until
  canceled       → blocked
  trial_expired  → blocked

Blocked clinics can still reach /api/billing/ (to add a card), /api/users/me/ and logout.
"""
import datetime
import os

from django.utils import timezone

TRIAL_DAYS = int(os.environ.get('TRIAL_DAYS', '14') or 14)
GRACE_DAYS = int(os.environ.get('BILLING_GRACE_DAYS', '3') or 3)

BLOCK_MESSAGES = {
    'trial_expired':         'Your trial has ended. Please add a payment method to continue.',
    'payment_past_due':      'Your payment is past due. Please update your card.',
    'subscription_canceled': 'Your subscription has been canceled. Please add a payment method to reactivate.',
}


def default_plan():
    from .models import Plan
    return Plan.objects.filter(is_active=True).order_by('price', 'id').first() or Plan.objects.order_by('id').first()


def new_trial_end(now=None):
    return (now or timezone.now()) + datetime.timedelta(days=TRIAL_DAYS)


# ── Access state ──────────────────────────────────────────────────────────────

def billing_state(clinic, now=None):
    """Returns (effective_status, block_code or None, warning_code or None)."""
    now = now or timezone.now()
    s = clinic.subscription_status
    if s == 'trialing':
        if clinic.trial_end and now >= clinic.trial_end and not clinic.stripe_subscription_id:
            return 'trial_expired', 'trial_expired', None
        return s, None, None
    if s == 'trial_expired':
        return s, 'trial_expired', None
    if s == 'past_due':
        if clinic.grace_until and now > clinic.grace_until:
            return s, 'payment_past_due', None
        return s, None, 'payment_past_due'
    if s == 'canceled':
        return s, 'subscription_canceled', None
    return s, None, None


def refresh_trial_status(clinic, now=None):
    """Stores trial_expired once the trial has run out (so lists/filters see it)."""
    status, _, _ = billing_state(clinic, now)
    if status == 'trial_expired' and clinic.subscription_status == 'trialing':
        type(clinic).objects.filter(pk=clinic.pk, subscription_status='trialing').update(subscription_status='trial_expired')
        clinic.subscription_status = 'trial_expired'
    return clinic


def serialize_plan(plan):
    if plan is None:
        return None
    return {
        'id':       plan.id,
        'name':     plan.name,
        'price':    float(plan.price),
        'currency': plan.currency,
        'interval': plan.interval,
        'limits':   plan.limits or {},
    }


def billing_payload(clinic, now=None):
    """Billing block used by GET /api/billing/status/, login, refresh and /me."""
    now = now or timezone.now()
    status, block, warning = billing_state(clinic, now)
    trial_days_left = None
    if status == 'trialing' and clinic.trial_end:
        trial_days_left = max((clinic.trial_end - now).days + (1 if (clinic.trial_end - now).seconds else 0), 0)
    next_billing = clinic.current_period_end
    if status == 'trialing' and clinic.stripe_subscription_id:
        next_billing = clinic.trial_end or next_billing
    if status in ('canceled', 'trial_expired'):
        next_billing = None
    return {
        'plan':                serialize_plan(clinic.plan),
        'subscription_status': status,
        'trial_end':           clinic.trial_end,
        'trial_days_left':     trial_days_left,
        'next_billing_date':   next_billing,
        'grace_until':         clinic.grace_until if status == 'past_due' else None,
        'has_payment_method':  bool(clinic.card_last4),
        'card': {
            'brand':     clinic.card_brand,
            'last4':     clinic.card_last4,
            'exp_month': clinic.card_exp_month,
            'exp_year':  clinic.card_exp_year,
        } if clinic.card_last4 else None,
        'access_blocked':      block is not None,
        'block_code':          block,
        'warning':             warning,
    }


# ── Stripe helpers ────────────────────────────────────────────────────────────

def stripe_client():
    import stripe
    key = os.environ.get('STRIPE_SECRET_KEY', '')
    if not key:
        return None
    stripe.api_key = key
    return stripe


def _ts(value):
    if not value:
        return None
    return datetime.datetime.fromtimestamp(int(value), tz=datetime.timezone.utc)


def _get(obj, key, default=None):
    try:
        value = obj.get(key, default) if hasattr(obj, 'get') else getattr(obj, key, default)
    except Exception:
        value = default
    return default if value is None else value


def period_end_of(sub):
    end = _get(sub, 'current_period_end')
    if not end:
        items = _get(_get(sub, 'items', {}), 'data', []) or []
        if items:
            end = _get(items[0], 'current_period_end')
    return _ts(end)


# Stripe subscription status → clinic subscription_status (None = leave unchanged)
STRIPE_STATUS_MAP = {
    'active':             'active',
    'trialing':           'trialing',
    'past_due':           'past_due',
    'unpaid':             'past_due',
    'canceled':           'canceled',
    'incomplete_expired': 'canceled',
    'incomplete':         None,       # waiting for the first payment / 3-D Secure
    'paused':             None,
}


def set_past_due(clinic, now=None):
    now = now or timezone.now()
    if clinic.subscription_status != 'past_due' or not clinic.grace_until:
        clinic.past_due_since = now
        clinic.grace_until = now + datetime.timedelta(days=GRACE_DAYS)
    clinic.subscription_status = 'past_due'


def set_active(clinic):
    clinic.subscription_status = 'active'
    clinic.past_due_since = None
    clinic.grace_until = None
    clinic.canceled_at = None


def apply_subscription(clinic, sub, now=None):
    """Copies a Stripe subscription's state onto the clinic (does not save)."""
    clinic.stripe_subscription_id = _get(sub, 'id', clinic.stripe_subscription_id)
    clinic.current_period_end = period_end_of(sub) or clinic.current_period_end
    mapped = STRIPE_STATUS_MAP.get(_get(sub, 'status'))
    if mapped == 'active':
        set_active(clinic)
    elif mapped == 'trialing':
        clinic.subscription_status = 'trialing'
        clinic.trial_end = _ts(_get(sub, 'trial_end')) or clinic.trial_end
    elif mapped == 'past_due':
        set_past_due(clinic, now)
    elif mapped == 'canceled':
        clinic.subscription_status = 'canceled'
        clinic.canceled_at = clinic.canceled_at or now or timezone.now()
    return clinic


def apply_card(clinic, payment_method):
    card = _get(payment_method, 'card', {}) or {}
    clinic.card_brand = str(_get(card, 'brand', ''))[:20]
    clinic.card_last4 = str(_get(card, 'last4', ''))[:4]
    clinic.card_exp_month = _get(card, 'exp_month') or None
    clinic.card_exp_year = _get(card, 'exp_year') or None
