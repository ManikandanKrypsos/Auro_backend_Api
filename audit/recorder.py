"""
Writes AuditEvent rows from model save / delete signals.

Clinical  — Patient, Appointment, SessionNote, ConsentRecord (documents): created / changed (only
            the fields that changed, before → after) / deleted.
Financial — Invoice created / voided / edited (not the automatic status changes a payment causes),
            Payment recorded, refund issued, payment (un)reconciled.
Stock     — every StockMovement (who used / wasted / received / returned / corrected what).

The actor is the logged-in user of the request (tenants.context), "System" when there is none
(webhooks, scheduled jobs). Recording never breaks the save that triggered it.
"""
import datetime
import decimal
import logging

from django.db import connection, transaction
from django.db.models import ForeignKey
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone

log = logging.getLogger('aura.audit')

ACTIONS = {
    # clinical
    'patient_created':            ('clinical', 'Patient created'),
    'patient_updated':            ('clinical', 'Patient record updated'),
    'patient_deleted':            ('clinical', 'Patient deleted'),
    'appointment_created':        ('clinical', 'Appointment booked'),
    'appointment_rescheduled':    ('clinical', 'Appointment rescheduled'),
    'appointment_status_changed': ('clinical', 'Appointment status changed'),
    'appointment_updated':        ('clinical', 'Appointment updated'),
    'appointment_deleted':        ('clinical', 'Appointment deleted'),
    'session_note_created':       ('clinical', 'Session note added'),
    'session_note_updated':       ('clinical', 'Session note edited'),
    'session_note_deleted':       ('clinical', 'Session note deleted'),
    'document_created':           ('clinical', 'Document added'),
    'document_signed':            ('clinical', 'Consent signed'),
    'document_updated':           ('clinical', 'Document updated'),
    'document_deleted':           ('clinical', 'Document deleted'),
    # financial
    'invoice_created':            ('financial', 'Invoice created'),
    'invoice_updated':            ('financial', 'Invoice edited'),
    'invoice_voided':             ('financial', 'Invoice voided'),
    'payment_recorded':           ('financial', 'Payment recorded'),
    'refund_issued':              ('financial', 'Refund issued'),
    'payment_reconciled':         ('financial', 'Payment reconciled'),
    'payment_unreconciled':       ('financial', 'Payment reconciliation undone'),
    'payment_deleted':            ('financial', 'Payment deleted'),
    # stock (one per movement type)
    'stock_used':                 ('stock', 'Stock used in treatment'),
    'stock_wastage':              ('stock', 'Stock wasted'),
    'stock_received':             ('stock', 'Stock received'),
    'stock_returned':             ('stock', 'Stock returned to supplier'),
    'stock_correction':           ('stock', 'Stock count corrected'),
    'stock_adjusted':             ('stock', 'Stock adjusted'),
    'stock_added':                ('stock', 'Stock added'),
    'stock_ordered':              ('stock', 'Stock ordered'),
}


def label(action):
    return ACTIONS.get(action, ('', action.replace('_', ' ').capitalize()))[1]


def _user_label(u):
    return (u.username or u.email.split('@')[0]) if u else ''


def _fmt(value):
    if value is None or isinstance(value, (bool, int, float, str, list, dict)):
        return value
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, datetime.datetime):
        return timezone.localtime(value).isoformat() if timezone.is_aware(value) else value.isoformat()
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    return str(value)


def _related_label(obj):
    if obj is None:
        return None
    if obj._meta.label == 'appointments.Appointment':
        return f'#{obj.pk}'                      # stable (its text form depends on the time zone)
    for attr in ('patient_id', 'name', 'username', 'invoice_number', 'title'):
        v = getattr(obj, attr, None)
        if v and not (attr == 'patient_id' and not isinstance(v, str)):
            return v if attr != 'username' else _user_label(obj)
    return str(obj)


def _file_label(value):
    """Files are shown by name, never as a link to the (possibly deleted) old file."""
    if not value:
        return None
    return value.rstrip('/').split('/')[-1].split('?')[0]


def snapshot(instance, fields, file_fields=()):
    out = {}
    for name in fields:
        field = instance._meta.get_field(name)
        if isinstance(field, ForeignKey):
            try:
                out[name] = _related_label(getattr(instance, name))
            except Exception:
                out[name] = getattr(instance, field.attname)
        elif name in file_fields:
            out[name] = _file_label(getattr(instance, name))
        else:
            out[name] = _fmt(getattr(instance, name))
    return out


def record(action, *, target_type, target_id, target_label='', patient=None, before=None, after=None,
           changed=None, summary='', actor=None, clinic_id=None, when=None, source='live', patient_label=None):
    from tenants.context import get_current_user
    from utils.request_id import get_request_id
    from .models import AuditEvent
    actor = actor or get_current_user()
    if actor is not None and not getattr(actor, 'is_authenticated', False):
        actor = None
    if actor is not None and actor.__class__.__name__ != 'User':
        actor = None                                   # console (platform) users aren't clinic users
    rid = get_request_id()
    AuditEvent.objects.create(
        clinic_id=clinic_id or getattr(patient, 'clinic_id', None) or (actor.clinic_id if actor else None),
        category=ACTIONS.get(action, ('clinical',))[0], action=action, summary=summary[:255],
        actor=actor, actor_label=_user_label(actor) if actor else 'System', actor_role=getattr(actor, 'role', '') or '',
        target_type=target_type, target_id=str(target_id)[:40], target_label=(target_label or '')[:255],
        patient=patient, patient_label=(patient_label if patient_label is not None else (patient.name if patient else ''))[:150],
        before=before, after=after, changed_fields=changed or [],
        request_id='' if rid == '-' else rid, source=source, created_at=when or timezone.now(),
    )


# ── per-model rules ──────────────────────────────────────────────────────────

class Spec:
    fields = ()
    file_fields = ()
    target_type = ''
    prefix = ''

    def target(self, obj):                       # (id, label)
        return obj.pk, str(obj)

    def patient(self, obj):
        return getattr(obj, 'patient', None)

    def clinic_id(self, obj):
        return getattr(obj, 'clinic_id', None) or getattr(self.patient(obj), 'clinic_id', None)

    def created(self, obj, after):               # → (action, summary) or None to skip
        return f'{self.prefix}_created', ''

    def updated(self, obj, before, after, changed):
        return f'{self.prefix}_updated', ''

    def deleted(self, obj, before):
        return f'{self.prefix}_deleted', ''


class PatientSpec(Spec):
    target_type, prefix = 'patient', 'patient'
    fields = ('name', 'phone', 'email', 'image', 'city', 'country', 'gender', 'dob', 'blood_type', 'allergies',
              'skin_type', 'contraindications', 'notes', 'category', 'marketing_source', 'tags')
    file_fields = ('image',)

    def target(self, obj):
        return obj.patient_id or f'Aura{obj.pk}', obj.name        # Aura id is assigned right after the insert

    def patient(self, obj):
        return obj


class AppointmentSpec(Spec):
    target_type, prefix = 'appointment', 'appointment'
    fields = ('date_time', 'duration', 'staff', 'room_fk', 'treatment', 'price_plan', 'package', 'status',
              'session_number', 'patient_arrived', 'consent_status', 'consent_form_url', 'notes')
    file_fields = ('consent_form_url',)
    SLOT = {'date_time', 'duration', 'staff', 'room_fk'}

    def target(self, obj):
        when = timezone.localtime(obj.date_time).strftime('%d %b %Y %H:%M') if obj.date_time else ''
        return obj.pk, f"{obj.treatment.name if obj.treatment_id and obj.treatment else 'Appointment'} · {when}"

    def created(self, obj, after):
        return 'appointment_created', ''

    def updated(self, obj, before, after, changed):
        if self.SLOT & set(changed):
            return 'appointment_rescheduled', ''
        if 'status' in changed:
            return 'appointment_status_changed', f"{before.get('status')} → {after.get('status')}"
        return 'appointment_updated', ''


class SessionNoteSpec(Spec):
    target_type, prefix = 'session_note', 'session_note'
    fields = ('appointment', 'therapist', 'treatment_name', 'skin_observation', 'session_notes', 'products_used',
              'recommended_to_patient', 'next_treatment', 'before_photo', 'after_photo')
    file_fields = ('before_photo', 'after_photo')

    def target(self, obj):
        return obj.pk, f"{obj.treatment_name or 'Session'} note"


class DocumentSpec(Spec):
    target_type, prefix = 'document', 'document'
    fields = ('type', 'title', 'appointment', 'file_url', 'notes', 'status', 'patient_signed', 'therapist_signed',
              'signed_date')
    file_fields = ('file_url',)

    def target(self, obj):
        return obj.pk, f'{obj.title} ({obj.get_type_display()})'

    def updated(self, obj, before, after, changed):
        if 'status' in changed and after.get('status') == 'signed':
            return 'document_signed', ''
        return 'document_updated', ''


class InvoiceSpec(Spec):
    target_type, prefix = 'invoice', 'invoice'
    fields = ('status', 'total', 'due_date', 'notes', 'patient', 'appointment')

    def target(self, obj):
        return obj.invoice_number or obj.pk, f'{obj.invoice_number} · €{obj.total}'

    def created(self, obj, after):
        return 'invoice_created', f'€{obj.total}'

    def updated(self, obj, before, after, changed):
        if 'status' in changed and after.get('status') == 'void':
            return 'invoice_voided', ''
        edited = [c for c in changed if c != 'status']    # status changes caused by payments are not edits
        if edited:
            return 'invoice_updated', ''
        return None


class PaymentSpec(Spec):
    target_type, prefix = 'payment', 'payment'
    fields = ('kind', 'amount', 'method', 'paid_at', 'reference', 'note', 'reason', 'receipt_number', 'reconciled',
              'reconciliation_ref', 'invoice')

    def target(self, obj):
        return obj.receipt_number or obj.pk, f'{obj.receipt_number or obj.get_kind_display()} · €{obj.amount} · {obj.method}'

    def patient(self, obj):
        return obj.invoice.patient if obj.invoice_id else None

    def created(self, obj, after):
        if obj.kind == 'refund':
            return 'refund_issued', f'€{obj.amount} refunded ({obj.method})'
        return 'payment_recorded', f'€{obj.amount} by {obj.method}'

    def updated(self, obj, before, after, changed):
        if 'reconciled' in changed:
            return ('payment_reconciled' if after.get('reconciled') else 'payment_unreconciled'), ''
        return None


class StockMovementSpec(Spec):
    target_type = 'inventory_item'
    fields = ('type', 'quantity', 'note', 'unit_cost', 'supplier', 'lot', 'appointment')

    def target(self, obj):
        return obj.item_id, obj.item.name if obj.item_id else ''

    def patient(self, obj):
        return obj.appointment.patient if obj.appointment_id and obj.appointment else None

    def created(self, obj, after):
        unit = obj.item.unit if obj.item_id else ''
        return f'stock_{obj.type}', f'{obj.quantity:+d} {unit}'.strip()

    def updated(self, obj, before, after, changed):
        return None

    def deleted(self, obj, before):
        return None


SPECS = {
    'patients.Patient': PatientSpec(),
    'appointments.Appointment': AppointmentSpec(),
    'patients.SessionNote': SessionNoteSpec(),
    'patients.ConsentRecord': DocumentSpec(),
    'payments.Invoice': InvoiceSpec(),
    'payments.Payment': PaymentSpec(),
    'inventory.StockMovement': StockMovementSpec(),
}


def record_reconciliation(payments, reconciled, reference=''):
    """Bulk (un)reconcile uses QuerySet.update(), which sends no signals — record each payment here."""
    spec = SPECS['payments.Payment']
    for p in payments:
        try:
            tid, tlabel = spec.target(p)
            after = {'reconciled': reconciled}
            if reconciled and reference:
                after['reconciliation_ref'] = reference[:120]
            record('payment_reconciled' if reconciled else 'payment_unreconciled', target_type='payment',
                   target_id=tid, target_label=tlabel, patient=spec.patient(p), before={'reconciled': not reconciled},
                   after=after, changed=['reconciled'], clinic_id=p.clinic_id)
        except Exception:
            log.exception('audit reconcile record failed for payment %s', p.pk)


# ── signal handlers ──────────────────────────────────────────────────────────

def _spec(sender):
    return SPECS.get(sender._meta.label)


def _before_save(sender, instance, raw=False, **kwargs):
    spec = _spec(sender)
    if spec is None or raw or not instance.pk:
        return
    try:
        old = sender._base_manager.filter(pk=instance.pk).first()
        instance._audit_before = snapshot(old, spec.fields, spec.file_fields) if old else None
    except Exception:
        log.exception('audit snapshot failed for %s %s', sender._meta.label, instance.pk)


def _record_created(sender, spec, instance):
    after = snapshot(instance, spec.fields, spec.file_fields)
    res = spec.created(instance, after)
    if not res:
        return
    action, summary = res
    tid, tlabel = spec.target(instance)
    actor = getattr(instance, 'created_by', None) if sender._meta.label == 'inventory.StockMovement' else None
    record(action, target_type=spec.target_type, target_id=tid, target_label=tlabel,
           patient=spec.patient(instance), after={k: v for k, v in after.items() if v not in (None, '', [], {})},
           summary=summary, actor=actor, clinic_id=spec.clinic_id(instance))


def _after_save(sender, instance, created, raw=False, **kwargs):
    spec = _spec(sender)
    if spec is None or raw:
        return
    try:
        if created and connection.in_atomic_block:
            # Inside a transaction the row is usually still being filled in (e.g. an invoice gets its
            # lines and total right after it is created): record "created" once, with the final values,
            # when the transaction commits, and ignore the saves in between.
            instance._audit_pending = True
            from tenants.context import get_current_user
            from utils.request_id import _request_id
            user, rid = get_current_user(), _request_id.get()

            def later(pk=instance.pk):
                from tenants.context import _current_user
                tok_u, tok_r = _current_user.set(user), _request_id.set(rid)
                try:
                    fresh = sender._base_manager.filter(pk=pk).first()
                    if fresh is not None:
                        _record_created(sender, spec, fresh)
                except Exception:
                    log.exception('audit record failed for %s %s', sender._meta.label, pk)
                finally:
                    _current_user.reset(tok_u)
                    _request_id.reset(tok_r)
                    instance._audit_pending = False
            transaction.on_commit(later)
            return
        if getattr(instance, '_audit_pending', False):
            return
        after = snapshot(instance, spec.fields, spec.file_fields)
        actor = getattr(instance, 'created_by', None) if sender._meta.label == 'inventory.StockMovement' else None
        if created or getattr(instance, '_audit_before', None) is None:
            res = spec.created(instance, after)
            before, changed = None, []
            after = {k: v for k, v in after.items() if v not in (None, '', [], {})}
        else:
            before_all = instance._audit_before
            changed = [k for k in spec.fields if before_all.get(k) != after.get(k)]
            if not changed:
                return
            res = spec.updated(instance, before_all, after, changed)
            before = {k: before_all.get(k) for k in changed}
            after = {k: after.get(k) for k in changed}
        if not res:
            return
        action, summary = res
        tid, tlabel = spec.target(instance)
        record(action, target_type=spec.target_type, target_id=tid, target_label=tlabel,
               patient=spec.patient(instance), before=before, after=after, changed=changed,
               summary=summary, actor=actor, clinic_id=spec.clinic_id(instance))
    except Exception:
        log.exception('audit record failed for %s %s', sender._meta.label, instance.pk)


def _after_delete(sender, instance, **kwargs):
    spec = _spec(sender)
    if spec is None:
        return
    try:
        before = snapshot(instance, spec.fields, spec.file_fields)
        res = spec.deleted(instance, before)
        if not res:
            return
        action, summary = res
        tid, tlabel = spec.target(instance)
        patient = spec.patient(instance)
        plabel = patient.name if patient is not None else ''
        if patient is not None and (sender._meta.label == 'patients.Patient' or
                                    not type(patient)._base_manager.filter(pk=patient.pk).exists()):
            patient = None                               # the patient row is gone; keep the name only
        record(action, target_type=spec.target_type, target_id=tid, target_label=tlabel, patient=patient,
               patient_label=plabel,
               before={k: v for k, v in before.items() if v not in (None, '', [], {})},
               summary=summary, clinic_id=spec.clinic_id(instance))
    except Exception:
        log.exception('audit delete record failed for %s %s', sender._meta.label, instance.pk)


pre_save.connect(_before_save, dispatch_uid='audit_pre_save')
post_save.connect(_after_save, dispatch_uid='audit_post_save')
post_delete.connect(_after_delete, dispatch_uid='audit_post_delete')
