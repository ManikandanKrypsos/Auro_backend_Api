"""
Recording Stripe payments for invoices — one place, used by the webhooks, the confirm endpoint and
the reconcile endpoint. Idempotent: a PaymentIntent is recorded at most once (Payment.reference),
so a webhook, a retry and a manual "Verify payment" can all run without double-counting.
"""
import logging
import os
from decimal import Decimal

from django.db import transaction

from . import invoicing as inv
from .models import Invoice, Payment

log = logging.getLogger('aura.stripe')


def stripe_api():
    import stripe
    stripe.api_key = stripe.api_key or os.environ.get('STRIPE_SECRET_KEY', '')
    return stripe


def plain(obj):
    """Stripe object → plain dict (works with old and new stripe-python, where objects stopped being dicts)."""
    if obj is None or type(obj) is dict:
        return obj
    for name in ('to_dict_recursive', 'to_dict'):
        fn = getattr(type(obj), name, None)
        if fn:
            return fn(obj)
    return dict(obj)


def _get(obj, key, default=None):
    try:
        v = obj.get(key, default) if hasattr(obj, 'get') else getattr(obj, key, default)
    except Exception:
        v = default
    return default if v is None else v


def invoice_for(appointment_id=None, invoice_id=None):
    if invoice_id:
        return Invoice._base_manager.filter(pk=invoice_id).first()
    if appointment_id:
        from appointments.models import Appointment
        appt = Appointment._base_manager.select_related('treatment', 'price_plan').filter(pk=appointment_id).first()
        return inv.invoice_for_appointment(appt) if appt else None
    return None


def record_stripe_payment(invoice, payment_intent_id, amount_cents, paid_at=None):
    """
    Returns (payment_or_None, outcome):
      'recorded'         new payment saved
      'already_recorded' this PaymentIntent was recorded before (webhook + verify both ran)
      'already_paid'     invoice had nothing left to pay — money received anyway, needs a look
    """
    if not payment_intent_id:
        return None, 'missing_payment_intent'
    with transaction.atomic():
        invoice = Invoice._base_manager.select_for_update().get(pk=invoice.pk)
        existing = Payment._base_manager.filter(invoice=invoice, kind='payment', reference=payment_intent_id).first()
        if existing:
            return existing, 'already_recorded'
        amount = inv.money(Decimal(amount_cents or 0) / 100)
        if invoice.balance_due <= 0 or invoice.status == 'void':
            log.warning('Stripe %s for invoice %s received %s but nothing was due', payment_intent_id,
                        invoice.invoice_number, amount)
            return None, 'already_paid'
        if amount > invoice.balance_due:
            log.warning('Stripe %s paid %s, more than the %s due on %s — recording the amount due',
                        payment_intent_id, amount, invoice.balance_due, invoice.invoice_number)
            amount = invoice.balance_due
        payment = inv.add_payment(invoice, amount, 'online', paid_at=paid_at, reference=payment_intent_id,
                                  note='Stripe')
        if not invoice.stripe_payment_intent_id:
            Invoice._base_manager.filter(pk=invoice.pk).update(stripe_payment_intent_id=payment_intent_id)
        return payment, 'recorded'


def apply_checkout_session(session):
    """A Checkout Session object (from a webhook or from Stripe directly) for an appointment / invoice."""
    session = plain(session)
    meta = _get(session, 'metadata', {}) or {}
    invoice = invoice_for(meta.get('appointment_id'), meta.get('invoice_id'))
    if invoice is None:
        return None, None, 'invoice_not_found'
    if _get(session, 'payment_status') != 'paid':
        return invoice, None, f"not_paid:{_get(session, 'payment_status') or _get(session, 'status')}"
    pi = _get(session, 'payment_intent')
    pi_id = pi if isinstance(pi, str) else _get(pi, 'id')
    payment, outcome = record_stripe_payment(invoice, pi_id, _get(session, 'amount_total'))
    return invoice, payment, outcome


def apply_payment_intent(intent):
    intent = plain(intent)
    meta = _get(intent, 'metadata', {}) or {}
    invoice = invoice_for(meta.get('appointment_id'), meta.get('invoice_id'))
    if invoice is None:
        return None, None, 'invoice_not_found'
    if _get(intent, 'status') != 'succeeded':
        return invoice, None, f"not_paid:{_get(intent, 'status')}"
    payment, outcome = record_stripe_payment(invoice, _get(intent, 'id'),
                                             _get(intent, 'amount_received') or _get(intent, 'amount'))
    return invoice, payment, outcome
