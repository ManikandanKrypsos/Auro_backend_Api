"""
One invoice for every existing appointment, so history shows up in the new invoice / payment
screens and revenue (now = money received) matches what was there before:

- line = the appointment's payment_amount (falls back to the price plan / treatment price;
  package sessions with no amount = 0), tax-inclusive at the clinic's default rate
- marked paid with no amount → total 0 (as before: it never counted as revenue)
- paid appointments     → one payment for the full amount, dated on the appointment
- refunded appointments → that payment plus a matching refund
- cancelled + unpaid    → void
"""
import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.db import migrations
from django.utils import timezone

CENT = Decimal('0.01')


def money(v):
    return Decimal(str(v or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def backfill(apps, schema_editor):
    Appointment = apps.get_model('appointments', 'Appointment')
    Clinic = apps.get_model('tenants', 'Clinic')
    Invoice = apps.get_model('payments', 'Invoice')
    InvoiceLine = apps.get_model('payments', 'InvoiceLine')
    Payment = apps.get_model('payments', 'Payment')
    InvoiceCounter = apps.get_model('payments', 'InvoiceCounter')

    rates = {c.id: Decimal(c.default_tax_rate) for c in Clinic.objects.all()}
    counters = {}
    done = set(Invoice.objects.exclude(appointment_id=None).values_list('appointment_id', flat=True))
    appts = (Appointment.objects.exclude(pk__in=done).select_related('treatment', 'price_plan')
             .order_by('clinic_id', 'date_time', 'id'))
    for a in appts.iterator():
        day = timezone.localtime(a.date_time).date() if a.date_time else timezone.localdate()
        key = (a.clinic_id, day.year)
        if key not in counters:
            c, _ = InvoiceCounter.objects.get_or_create(clinic_id=a.clinic_id, year=day.year)
            counters[key] = c
        counter = counters[key]
        counter.last += 1
        counter.save(update_fields=['last'])

        note = ''
        if a.payment_amount is not None:
            price = money(a.payment_amount)
        elif a.payment_status in ('paid', 'refunded'):
            # marked paid without an amount: keep it at 0 so past revenue doesn't change
            price, note = Decimal('0.00'), 'Marked paid before invoices, with no amount recorded.'
        elif a.package_id:
            price = Decimal('0.00')
        elif a.price_plan_id and a.price_plan and a.price_plan.price:
            price = money(a.price_plan.price)
        elif a.treatment_id and a.treatment and a.treatment.price:
            price = money(a.treatment.price)
        else:
            price = Decimal('0.00')
        rate = rates.get(a.clinic_id, Decimal('7'))
        tax = money(price - price / (1 + rate / 100)) if rate else Decimal('0.00')

        paid = a.payment_status in ('paid', 'refunded') and price > 0
        if a.payment_status == 'refunded' and price > 0:
            status, amount_paid, balance = 'refunded', Decimal('0.00'), Decimal('0.00')
        elif a.status == 'cancelled' and not paid:
            status, amount_paid, balance = 'void', Decimal('0.00'), Decimal('0.00')
        elif price <= 0:
            status, amount_paid, balance = 'no_charge', Decimal('0.00'), Decimal('0.00')
        elif paid:
            status, amount_paid, balance = 'paid', price, Decimal('0.00')
        else:
            status, amount_paid, balance = 'open', Decimal('0.00'), price

        inv = Invoice.objects.create(
            clinic_id=a.clinic_id, patient_id=a.patient_id, appointment_id=a.id,
            invoice_number=f'INV-{day.year}-{counter.last:04d}', issue_date=day, due_date=day,
            status=status, voided_automatically=(status == 'void'), notes=note,
            subtotal=price - tax, tax_amount=tax, total=price, amount_paid=amount_paid, balance_due=balance,
        )
        name = (a.treatment.name if a.treatment_id and a.treatment else 'Appointment')
        if a.package_id:
            name += ' (package session)'
        InvoiceLine.objects.create(invoice=inv, position=0, description=name[:255], treatment_id=a.treatment_id,
                                   quantity=1, unit_price=price, tax_rate=rate, line_total=price, tax_amount=tax,
                                   from_appointment=True)
        if paid:
            method = 'online' if a.payment_type == 'online' else 'cash'
            ref = a.notes.split('stripe_pi:')[1].strip()[:120] if a.notes and a.notes.startswith('stripe_pi:') else ''
            when = a.date_time or timezone.now()
            Payment.objects.create(clinic_id=a.clinic_id, invoice=inv, kind='payment', amount=price, method=method,
                                   paid_at=when, reference=ref, note='Recorded before invoices existed')
            if a.payment_status == 'refunded':
                Payment.objects.create(clinic_id=a.clinic_id, invoice=inv, kind='refund', amount=price,
                                       method=method, paid_at=when, note='Refunded before invoices existed')


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_invoices'),
        ('appointments', '0002_appointment_clinic'),
        ('tenants', '0006_invoice_settings'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
