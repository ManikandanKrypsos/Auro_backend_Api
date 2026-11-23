"""
Existing payment records get receipt numbers (RCPT-<year>-<n>, refunds REF-<year>-<n>, per clinic,
in date order); existing refunds are linked to the payment they refund and count as credited on
their invoice (they were full refunds of cancelled appointments), so those invoices no longer
show a balance due.
"""
from django.db import migrations
from django.db.models import Sum


def number_payments(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')
    Invoice = apps.get_model('payments', 'Invoice')
    Counter = apps.get_model('payments', 'InvoiceCounter')
    from django.utils import timezone
    counters = {}
    for p in Payment.objects.filter(receipt_number='').order_by('clinic_id', 'paid_at', 'id').iterator():
        year = timezone.localtime(p.paid_at).year
        kind = 'refund' if p.kind == 'refund' else 'receipt'
        key = (p.clinic_id, year, kind)
        if key not in counters:
            counters[key], _ = Counter.objects.get_or_create(clinic_id=p.clinic_id, year=year, kind=kind)
        c = counters[key]
        c.last += 1
        c.save(update_fields=['last'])
        p.receipt_number = f"{'REF' if kind == 'refund' else 'RCPT'}-{year}-{c.last:04d}"
        if p.kind == 'refund' and not p.refund_of_id:
            p.refund_of = (Payment.objects.filter(invoice_id=p.invoice_id, kind='payment')
                           .order_by('-paid_at', '-id').first())
            p.adjusts_invoice = True
            p.reason = p.reason or p.note
        p.save()
    from decimal import Decimal
    for inv in Invoice.objects.filter(payments__kind='refund').distinct():
        inv.credited = Payment.objects.filter(invoice=inv, kind='refund', adjusts_invoice=True) \
            .aggregate(t=Sum('amount'))['t'] or Decimal('0')
        # refunds now also lower what is owed: a refunded invoice no longer shows a balance due
        if inv.status != 'void':
            inv.balance_due = max(inv.total - inv.credited - inv.amount_paid, Decimal('0'))
            if inv.status == 'paid' and inv.credited > 0:
                inv.status = 'partially_refunded'
        inv.save(update_fields=['credited', 'balance_due', 'status'])


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_refunds_receipts'),
    ]

    operations = [
        migrations.RunPython(number_payments, migrations.RunPython.noop),
    ]
