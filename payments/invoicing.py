"""
Invoice / payment rules. Everything that changes money goes through here so the invoice totals,
its status and the appointment's legacy payment fields (payment_amount / payment_status /
payment_type, still used by older screens) always agree.

Prices are tax-inclusive. A line's tax = line_total - line_total / (1 + rate/100).
"""
import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Invoice, InvoiceCounter, InvoiceLine, Payment

CENT = Decimal('0.01')
METHODS = dict(Payment.METHOD_CHOICES)


def money(value):
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def clinic_settings(clinic_id):
    from tenants.models import Clinic
    c = Clinic.objects.filter(pk=clinic_id).only('default_tax_rate', 'invoice_due_days').first()
    return (c.default_tax_rate if c else Decimal('7'), c.invoice_due_days if c else 0)


PREFIX = {'invoice': 'INV', 'receipt': 'RCPT', 'refund': 'REF'}


def next_number(clinic_id, year, kind='invoice'):
    with transaction.atomic():
        counter, _ = InvoiceCounter.objects.select_for_update().get_or_create(clinic_id=clinic_id, year=year, kind=kind)
        counter.last += 1
        counter.save(update_fields=['last'])
        return f'{PREFIX[kind]}-{year}-{counter.last:04d}'


def next_invoice_number(clinic_id, year):
    return next_number(clinic_id, year, 'invoice')


def _receipt_number(clinic_id, paid_at, kind):
    return next_number(clinic_id, timezone.localtime(paid_at).year, 'refund' if kind == 'refund' else 'receipt')


def line_amounts(line):
    line.line_total = money(Decimal(line.quantity) * Decimal(line.unit_price))
    rate = Decimal(line.tax_rate or 0)
    net = (line.line_total / (1 + rate / 100)) if rate else line.line_total
    line.tax_amount = money(line.line_total - net)
    return line


def recalc(invoice, sync=True):
    """Totals from lines, amount_paid from payments, then status. Saves the invoice."""
    lines = list(InvoiceLine.objects.filter(invoice=invoice))
    invoice.total = money(sum((l.line_total for l in lines), Decimal(0)))
    invoice.tax_amount = money(sum((l.tax_amount for l in lines), Decimal(0)))
    invoice.subtotal = invoice.total - invoice.tax_amount
    paid = money(Payment.objects.filter(invoice=invoice, kind='payment').aggregate(t=Sum('amount'))['t'])
    refunds = Payment.objects.filter(invoice=invoice, kind='refund')
    refunded = money(refunds.aggregate(t=Sum('amount'))['t'])
    invoice.credited = money(refunds.filter(adjusts_invoice=True).aggregate(t=Sum('amount'))['t'])
    invoice.amount_paid = paid - refunded
    if invoice.status == 'void':
        invoice.balance_due = Decimal('0.00')
    else:
        invoice.balance_due = max(invoice.total - invoice.credited - invoice.amount_paid, Decimal('0.00'))
        if paid > 0 and invoice.amount_paid <= 0 and invoice.balance_due <= 0:
            invoice.status = 'refunded'
        elif invoice.total <= 0 and paid <= 0:
            invoice.status = 'no_charge'
        elif invoice.balance_due <= 0:
            invoice.status = 'partially_refunded' if refunded > 0 else 'paid'
        elif invoice.amount_paid > 0:
            invoice.status = 'partially_paid'
        else:
            invoice.status = 'open'
    invoice.save()
    if sync:
        sync_appointment(invoice)
    return invoice


def sync_appointment(invoice):
    """Copies the invoice state onto the appointment's legacy payment fields (no save signals)."""
    if not invoice.appointment_id:
        return
    from appointments.models import Appointment
    fields = {}
    if invoice.status != 'void':
        fields['payment_amount'] = invoice.total
    if invoice.status in ('paid', 'partially_refunded'):
        fields['payment_status'] = 'paid'
    elif invoice.status == 'refunded':
        fields['payment_status'] = 'refunded'
    elif invoice.status in ('open', 'partially_paid'):
        fields['payment_status'] = 'pending'
    last = Payment.objects.filter(invoice=invoice, kind='payment').order_by('-paid_at', '-id').first()
    if last:
        fields['payment_type'] = 'online' if last.method == 'online' else 'cash'
    if fields:
        Appointment.objects.filter(pk=invoice.appointment_id).update(**fields)


# ── Appointment invoices ──────────────────────────────────────────────────────

def appointment_price(appt):
    if appt.package_id and appt.payment_amount in (None, 0):
        return Decimal('0.00')                  # a session already paid for through a package
    if appt.payment_amount is not None:
        return money(appt.payment_amount)
    if appt.price_plan_id and appt.price_plan and appt.price_plan.price:
        return money(appt.price_plan.price)
    if appt.treatment_id and appt.treatment and getattr(appt.treatment, 'price', None):
        return money(appt.treatment.price)
    return Decimal('0.00')


def _local_date(dt):
    return timezone.localtime(dt).date() if dt else timezone.localdate()


def create_for_appointment(appt, user=None):
    if Invoice.objects.model._base_manager.filter(appointment_id=appt.pk).exists():
        return Invoice.objects.model._base_manager.get(appointment_id=appt.pk)
    rate, _ = clinic_settings(appt.clinic_id)
    day = _local_date(appt.date_time)
    with transaction.atomic():
        invoice = Invoice.objects.create(
            clinic_id=appt.clinic_id, patient_id=appt.patient_id, appointment=appt,
            invoice_number=next_invoice_number(appt.clinic_id, day.year),
            issue_date=day, due_date=day, created_by=user,
        )
        name = appt.treatment.name if appt.treatment_id and appt.treatment else 'Appointment'
        if appt.package_id:
            name += ' (package session)'
        line = InvoiceLine(invoice=invoice, position=0, description=name[:255], treatment_id=appt.treatment_id,
                           quantity=1, unit_price=appointment_price(appt), tax_rate=rate, from_appointment=True)
        line_amounts(line).save()
        if appt.status == 'cancelled':
            invoice.status, invoice.voided_automatically = 'void', True
        recalc(invoice)
        # carry over an appointment that was already marked paid / refunded the old way
        _apply_legacy_status(invoice, appt, user)
    return invoice


def invoice_for_appointment(appt, user=None):
    inv = Invoice.objects.model._base_manager.filter(appointment_id=appt.pk).first()
    return inv or create_for_appointment(appt, user)


def _apply_legacy_status(invoice, appt, user=None, note='Marked paid on the appointment'):
    """Older screens still set appointment.payment_status directly — turn that into real records."""
    if appt.payment_status == 'paid' and invoice.balance_due > 0 and invoice.status != 'void':
        reference = ''
        if appt.notes and appt.notes.startswith('stripe_pi:'):
            reference = appt.notes.split('stripe_pi:')[1].strip()[:120]
        add_payment(invoice, invoice.balance_due, 'online' if appt.payment_type == 'online' else 'cash',
                    user=user, reference=reference, note=note)
    elif appt.payment_status == 'refunded' and invoice.amount_paid > 0:
        add_refund(invoice, invoice.amount_paid, method=_last_method(invoice), user=user,
                   note='Refunded on the appointment')
    elif appt.payment_status == 'pending' and invoice.status in ('paid', 'refunded', 'partially_refunded'):
        sync_appointment(invoice)          # the invoice is the record of truth: put the appointment back


def _last_method(invoice):
    last = Payment.objects.filter(invoice=invoice, kind='payment').order_by('-paid_at', '-id').first()
    return last.method if last else 'cash'


def appointment_saved(appt, created):
    """Called after every Appointment save (signal)."""
    if created:
        create_for_appointment(appt)
        return
    invoice = invoice_for_appointment(appt)
    changed = False
    if appt.status == 'cancelled' and invoice.status in ('open', 'no_charge') and invoice.amount_paid <= 0:
        invoice.status, invoice.voided_automatically = 'void', True
        changed = True
    elif appt.status != 'cancelled' and invoice.status == 'void' and invoice.voided_automatically:
        invoice.status, invoice.voided_automatically = 'open', False
        changed = True
    # price edited on the appointment → the automatic line follows, as long as nothing was paid
    line = InvoiceLine.objects.filter(invoice=invoice, from_appointment=True).first()
    if line and not invoice.payments.exists() and appt.payment_amount is not None \
            and money(appt.payment_amount) != line.unit_price and line.quantity == 1:
        line.unit_price = money(appt.payment_amount)
        line_amounts(line).save()
        changed = True
    if invoice.status in ('open', 'partially_paid', 'no_charge') and not invoice.payments.exists():
        day = _local_date(appt.date_time)
        if invoice.due_date != day or invoice.issue_date != day:
            invoice.issue_date = invoice.due_date = day
            changed = True
    if changed:
        recalc(invoice)
    _apply_legacy_status(invoice, appt)


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentError(Exception):
    def __init__(self, code, message, field=None):
        super().__init__(message)
        self.code, self.message, self.field = code, message, field


def add_payment(invoice, amount, method, user=None, paid_at=None, reference='', note=''):
    amount = money(amount)
    if amount <= 0:
        raise PaymentError('invalid_amount', 'Amount must be more than 0.', 'amount')
    if method not in METHODS:
        raise PaymentError('invalid_method', f'Use one of: {", ".join(METHODS)}.', 'method')
    if invoice.status == 'void':
        raise PaymentError('invoice_void', 'This invoice is void.')
    if amount > invoice.balance_due:
        raise PaymentError('exceeds_balance', f'Only {invoice.balance_due} is due on this invoice.', 'amount')
    paid_at = paid_at or timezone.now()
    p = Payment.objects.create(clinic_id=invoice.clinic_id, invoice=invoice, kind='payment', amount=amount,
                               method=method, paid_at=paid_at, reference=(reference or '')[:120],
                               note=(note or '')[:255], created_by=user,
                               receipt_number=_receipt_number(invoice.clinic_id, paid_at, 'payment'))
    recalc(invoice)
    return p


def add_refund(invoice, amount, method, user=None, paid_at=None, reference='', note=''):
    """Refund recorded by the older appointment screens (money already returned): spread over the
    invoice's payments, newest first."""
    amount = money(amount)
    if amount <= 0:
        raise PaymentError('invalid_amount', 'Amount must be more than 0.', 'amount')
    if amount > invoice.amount_paid:
        raise PaymentError('exceeds_paid', f'Only {invoice.amount_paid} has been paid on this invoice.', 'amount')
    last = None
    for p in Payment.objects.filter(invoice=invoice, kind='payment').order_by('-paid_at', '-id'):
        part = min(refundable(p), amount)
        if part > 0:
            last = refund_payment(p, part, reason=note or 'Refund', user=user, record_only=True, paid_at=paid_at,
                                  reference=reference)
            amount -= part
        if amount <= 0:
            break
    return last


def refundable(payment):
    """How much of a payment can still be refunded."""
    if payment.kind != 'payment':
        return Decimal('0.00')
    done = payment.refunds.aggregate(t=Sum('amount'))['t'] or 0
    return max(money(payment.amount) - money(done), Decimal('0.00'))


def refund_payment(payment, amount=None, reason='', user=None, adjust_invoice=True, record_only=False,
                   paid_at=None, reference=''):
    """
    Refund part or all of one payment. Online (Stripe) payments are refunded through Stripe
    unless record_only (money already returned some other way). adjust_invoice=True (default)
    also lowers what the patient owes; False puts the refunded amount back on the balance.
    """
    if payment.kind != 'payment':
        raise PaymentError('not_a_payment', 'Only payments can be refunded.')
    available = refundable(payment)
    amount = available if amount in (None, '') else money(amount)
    if available <= 0:
        raise PaymentError('already_refunded', 'This payment has already been fully refunded.')
    if amount <= 0:
        raise PaymentError('invalid_amount', 'Amount must be more than 0.', 'amount')
    if amount > available:
        raise PaymentError('exceeds_refundable', f'Only {available} of this payment can still be refunded.', 'amount')
    stripe_ref = ''
    if payment.method == 'online' and not record_only:
        if not (payment.reference or '').startswith('pi_'):
            raise PaymentError('stripe_reference_missing',
                               'This online payment has no Stripe reference, so it can\'t be refunded automatically. '
                               'Refund it in Stripe, then record it with record_only: true.')
        import os
        import stripe
        stripe.api_key = stripe.api_key or os.environ.get('STRIPE_SECRET_KEY', '')
        try:
            r = stripe.Refund.create(payment_intent=payment.reference, amount=int(amount * 100),
                                     metadata={'aura_payment_id': str(payment.id), 'reason': (reason or '')[:200]})
        except stripe.error.StripeError as e:
            raise PaymentError('stripe_error', getattr(e, 'user_message', None) or 'Stripe could not refund this payment.')
        if r.get('status') not in ('succeeded', 'pending'):
            raise PaymentError('stripe_error', f"Stripe refund {r.get('status')}.")
        stripe_ref = r.get('id', '')
    paid_at = paid_at or timezone.now()
    refund = Payment.objects.create(
        clinic_id=payment.clinic_id, invoice=payment.invoice, kind='refund', amount=amount, method=payment.method,
        paid_at=paid_at, reference=(stripe_ref or reference or '')[:120], reason=(reason or '')[:255],
        note=(reason or '')[:255], refund_of=payment, adjusts_invoice=adjust_invoice, created_by=user,
        receipt_number=_receipt_number(payment.clinic_id, paid_at, 'refund'),
    )
    recalc(payment.invoice)
    return refund
