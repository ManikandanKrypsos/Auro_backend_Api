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


def next_invoice_number(clinic_id, year):
    with transaction.atomic():
        counter, _ = InvoiceCounter.objects.select_for_update().get_or_create(clinic_id=clinic_id, year=year)
        counter.last += 1
        counter.save(update_fields=['last'])
        return f'INV-{year}-{counter.last:04d}'


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
    paid = Payment.objects.filter(invoice=invoice, kind='payment').aggregate(t=Sum('amount'))['t'] or 0
    refunded = Payment.objects.filter(invoice=invoice, kind='refund').aggregate(t=Sum('amount'))['t'] or 0
    invoice.amount_paid = money(paid) - money(refunded)
    if invoice.status == 'void':
        invoice.balance_due = Decimal('0.00')
    else:
        invoice.balance_due = max(invoice.total - invoice.amount_paid, Decimal('0.00'))
        if paid and invoice.amount_paid <= 0:
            invoice.status = 'refunded'
        elif invoice.total <= 0 and not paid:
            invoice.status = 'no_charge'
        elif invoice.balance_due <= 0:
            invoice.status = 'paid'
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
    if invoice.status == 'paid':
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
    elif appt.payment_status == 'pending' and invoice.status in ('paid', 'refunded'):
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
    p = Payment.objects.create(clinic_id=invoice.clinic_id, invoice=invoice, kind='payment', amount=amount,
                               method=method, paid_at=paid_at or timezone.now(), reference=(reference or '')[:120],
                               note=(note or '')[:255], created_by=user)
    recalc(invoice)
    return p


def add_refund(invoice, amount, method, user=None, paid_at=None, reference='', note=''):
    amount = money(amount)
    if amount <= 0:
        raise PaymentError('invalid_amount', 'Amount must be more than 0.', 'amount')
    if amount > invoice.amount_paid:
        raise PaymentError('exceeds_paid', f'Only {invoice.amount_paid} has been paid on this invoice.', 'amount')
    p = Payment.objects.create(clinic_id=invoice.clinic_id, invoice=invoice, kind='refund', amount=amount,
                               method=method if method in METHODS else 'other', paid_at=paid_at or timezone.now(),
                               reference=(reference or '')[:120], note=(note or '')[:255], created_by=user)
    recalc(invoice)
    return p
