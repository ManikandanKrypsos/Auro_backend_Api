"""
Starts the audit trail with what the app already recorded: payments, refunds and reconciliations,
invoices (created / voided), every stock movement and patient registrations. These rows have
source="backfill". Field-level history of clinical edits did not exist before, so it starts now.
"""
from django.db import migrations


def _who(u):
    return (u.username or u.email.split('@')[0]) if u else 'System'


def forwards(apps, schema_editor):
    Event = apps.get_model('audit', 'AuditEvent')
    Payment = apps.get_model('payments', 'Payment')
    Invoice = apps.get_model('payments', 'Invoice')
    Movement = apps.get_model('inventory', 'StockMovement')
    Patient = apps.get_model('patients', 'Patient')
    batch = []

    def add(**kw):
        actor = kw.pop('actor', None)
        patient = kw.pop('patient', None)
        batch.append(Event(actor=actor, actor_label=_who(actor), actor_role=(getattr(actor, 'role', '') or ''),
                           patient=patient, patient_label=(patient.name if patient else '')[:150],
                           source='backfill', **kw))
        if len(batch) >= 500:
            Event.objects.bulk_create(batch)
            batch.clear()

    for p in Patient.objects.select_related('created_by').iterator():
        add(clinic_id=p.clinic_id, category='clinical', action='patient_created', target_type='patient',
            target_id=p.patient_id or str(p.pk), target_label=p.name, patient=p, actor=p.created_by,
            created_at=p.created_at)

    for inv in Invoice.objects.select_related('created_by', 'patient').iterator():
        label = f'{inv.invoice_number} · €{inv.total}'
        add(clinic_id=inv.clinic_id, category='financial', action='invoice_created', target_type='invoice',
            target_id=inv.invoice_number or str(inv.pk), target_label=label, patient=inv.patient,
            actor=inv.created_by, summary=f'€{inv.total}', created_at=inv.created_at)
        if inv.status == 'void':
            add(clinic_id=inv.clinic_id, category='financial', action='invoice_voided', target_type='invoice',
                target_id=inv.invoice_number or str(inv.pk), target_label=label, patient=inv.patient,
                actor=None if inv.voided_automatically else inv.created_by,
                summary='Appointment cancelled' if inv.voided_automatically else '',
                before={'status': 'open'}, after={'status': 'void'}, changed_fields=['status'],
                created_at=inv.updated_at)

    for pay in Payment.objects.select_related('created_by', 'reconciled_by', 'invoice__patient').iterator():
        patient = pay.invoice.patient if pay.invoice_id else None
        label = f"{pay.receipt_number or pay.kind} · €{pay.amount} · {pay.method}"
        refund = pay.kind == 'refund'
        add(clinic_id=pay.clinic_id, category='financial', action='refund_issued' if refund else 'payment_recorded',
            target_type='payment', target_id=pay.receipt_number or str(pay.pk), target_label=label,
            patient=patient, actor=pay.created_by,
            summary=f'€{pay.amount} refunded ({pay.method})' if refund else f'€{pay.amount} by {pay.method}',
            after={'amount': str(pay.amount), 'method': pay.method, 'reference': pay.reference,
                   'reason': pay.reason or None}, created_at=pay.created_at)
        if pay.reconciled and pay.reconciled_at:
            add(clinic_id=pay.clinic_id, category='financial', action='payment_reconciled', target_type='payment',
                target_id=pay.receipt_number or str(pay.pk), target_label=label, patient=patient,
                actor=pay.reconciled_by, before={'reconciled': False}, after={'reconciled': True},
                changed_fields=['reconciled'], created_at=pay.reconciled_at)

    for m in Movement.objects.select_related('created_by', 'item', 'lot', 'appointment__patient').iterator():
        add(clinic_id=m.clinic_id, category='stock', action=f'stock_{m.type}', target_type='inventory_item',
            target_id=str(m.item_id), target_label=m.item.name if m.item_id else '',
            patient=m.appointment.patient if m.appointment_id else None, actor=m.created_by,
            summary=f'{m.quantity:+d} {m.item.unit if m.item_id else ""}'.strip(),
            after={k: v for k, v in {'type': m.type, 'quantity': m.quantity, 'note': m.note or None,
                                     'lot': (m.lot.lot_number or str(m.lot_id)) if m.lot_id else None,
                                     'appointment': m.appointment_id}.items() if v not in (None, '')},
            created_at=m.created_at)
    if batch:
        Event.objects.bulk_create(batch)


def backwards(apps, schema_editor):
    apps.get_model('audit', 'AuditEvent').objects.filter(source='backfill').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('audit', '0001_initial'),
        ('payments', '0006_stripe_ids'),
        ('inventory', '0008_stockmovement_returned_type'),
        ('patients', '0006_documents'),
    ]
    operations = [migrations.RunPython(forwards, backwards)]
