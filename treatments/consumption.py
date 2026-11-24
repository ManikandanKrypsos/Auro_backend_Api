"""
Product usage per appointment.

The treatment's consumables are a template ("recipe") only — they never take stock by themselves.
Stock is deducted only when the therapist confirms what was actually used in the session
(confirm_usage, called from POST /api/appointments/<id>/consumption/). The recipe pre-fills that
form (prefill).

Rules agreed with the clinic:
- Not enough stock → the confirmation is still saved; whatever is in stock is deducted, the rest is
  recorded as a shortfall, the response carries a warning and admins get a `stock_shortfall`
  notification.
- Lot items: the chosen lot first, then earliest-expiring lots, then stock not in any lot. One stock
  movement per lot, so it can be put back into the same lot.
- Confirming again (an edit) puts the previous usage back and records the new one.
- If the appointment leaves in_session / completed (cancelled, no-show, back to upcoming), the
  confirmed usage is put back.
"""
import logging

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

log = logging.getLogger('aura.consumption')

AUTO = 'Session usage: '                # note prefix on movements made here
CONFIRMABLE = ('in_session', 'completed')


def _name(u):
    return (u.username or u.email.split('@')[0]) if u else None


def active_record(appt):
    from .models import SessionConsumption
    return SessionConsumption.objects.filter(appointment=appt, reversed=False).order_by('-id').first()


# ── deduct / put back ────────────────────────────────────────────────────────

def _take(item, quantity, appt, user, note, lot=None):
    """Deduct `quantity` (≤ current stock). Returns the first movement."""
    from inventory.models import Lot
    from inventory.services import remove_from_item
    first, left = None, quantity
    if item.track_lots:
        lots = list(Lot.objects.select_for_update().filter(item=item, quantity_remaining__gt=0)
                    .order_by('expiry_date', 'received_at'))
        if lot is not None:
            lots.sort(key=lambda l: l.pk != lot.pk)          # chosen lot first
        for l in lots:
            if left <= 0:
                break
            n = min(l.quantity_remaining, left)
            m = remove_from_item(item, n, 'used', user=user, note=note, lot=l, appointment=appt)
            first, left = first or m, left - n
    if left > 0:
        m = remove_from_item(item, left, 'used', user=user, note=note, appointment=appt)
        first = first or m
    return first


def _put_back(record, user, reason):
    from inventory.models import InventoryItem, Lot, StockMovement
    from inventory.services import add_correction
    note = f'Returned: {reason}'[:255]
    for line in record.lines.all():
        if line.deducted <= 0 or not line.movement_id:
            continue
        item = InventoryItem.objects.select_for_update().get(pk=line.item_id)
        moves = StockMovement.objects.filter(
            appointment_id=record.appointment_id, item_id=line.item_id, type='used',
            note__startswith=AUTO, id__gte=line.movement_id).order_by('id')
        left = line.deducted
        for m in moves:
            n = min(-m.quantity, left)
            if n <= 0:
                break
            lot = Lot.objects.select_for_update().get(pk=m.lot_id) if m.lot_id else None
            add_correction(item, n, user=user, lot=lot, appointment=record.appointment, note=note)
            left -= n
        if left > 0:
            add_correction(item, left, user=user, appointment=record.appointment, note=note)
    record.reversed = True
    record.reversed_at = timezone.now()
    record.save(update_fields=['reversed', 'reversed_at'])


def confirm_usage(appt, lines, user, note=''):
    """
    lines: [(item, quantity, lot_or_None)] — already validated.
    Replaces any earlier confirmation. Returns the new SessionConsumption.
    """
    from inventory.models import InventoryItem
    from .models import AppointmentConsumption, SessionConsumption, TreatmentConsumable
    planned = dict(TreatmentConsumable.objects.filter(treatment_id=appt.treatment_id)
                   .values_list('item_id', 'quantity')) if appt.treatment_id else {}
    treatment = appt.treatment.name if appt.treatment_id and appt.treatment else 'session'
    short = []
    with transaction.atomic():
        old = SessionConsumption.objects.select_for_update().filter(appointment=appt, reversed=False)
        for rec in old:
            _put_back(rec, user, f'usage for appointment #{appt.id} was edited')
        record = SessionConsumption.objects.create(appointment=appt, confirmed_by=user, note=note[:255])
        for item, qty, lot in lines:
            item = InventoryItem.objects.select_for_update().get(pk=item.pk)
            line = AppointmentConsumption(record=record, item=item, planned=planned.get(item.id, 0),
                                          quantity=qty, lot=lot, unit_cost=item.cost_per_unit or 0)
            take = min(qty, max(item.current_stock, 0))
            if take > 0:
                line.movement = _take(item, take, appt, user, f'{AUTO}{treatment} (appointment #{appt.id})', lot)
                line.deducted = take
            line.shortfall = qty - take
            if line.shortfall:
                short.append((item, line.shortfall))
            line.save()
    if short:
        _notify_shortfall(appt, short)
    return record


def appointment_saved(appt):
    """post_save hook: put the stock back if the appointment is no longer in session / completed."""
    if appt.status in CONFIRMABLE:
        return
    rec = active_record(appt)
    if rec:
        with transaction.atomic():
            _put_back(rec, None, f'appointment #{appt.id} is now {appt.status}')


def _notify_shortfall(appt, short):
    from notifications import service as notify
    patient = appt.patient.name if appt.patient_id and appt.patient else 'a patient'
    treatment = appt.treatment.name if appt.treatment_id and appt.treatment else 'treatment'
    parts = ', '.join(f'{item.name} ({qty} {item.unit} short)' for item, qty in short)
    notify.notify(notify.clinic_admins(appt.clinic_id), 'stock_shortfall',
                  f'Not enough stock for {patient}\'s {treatment}: {parts}. Please check the inventory.',
                  {'appointment_id': appt.id, 'item_ids': [item.id for item, _ in short]}, actor=None)


# ── read ─────────────────────────────────────────────────────────────────────

def _lots(item):
    from inventory.models import Lot
    if not item.track_lots:
        return None
    return [{'id': l.id, 'lot_number': l.lot_number, 'expiry_date': str(l.expiry_date) if l.expiry_date else None,
             'quantity_remaining': l.quantity_remaining}
            for l in Lot.objects.filter(item=item, quantity_remaining__gt=0).order_by('expiry_date', 'received_at')]


def prefill(appt):
    """What the confirm form should start with: the treatment's consumables, minus anything already
    logged by hand for this appointment."""
    from inventory.models import StockMovement
    from .models import TreatmentConsumable
    if not appt.treatment_id:
        return []
    logged = dict(StockMovement.objects.filter(appointment=appt, type='used').exclude(note__startswith=AUTO)
                  .values('item_id').annotate(t=Sum('quantity')).values_list('item_id', 't'))
    out = []
    for c in TreatmentConsumable.objects.filter(treatment_id=appt.treatment_id).select_related('item'):
        already = -(logged.get(c.item_id) or 0)
        cost = float(c.item.cost_per_unit or 0)
        qty = max(c.quantity - already, 0)
        out.append({'item_id': c.item_id, 'item_name': c.item.name, 'unit': c.item.unit,
                    'planned': c.quantity, 'already_logged': already, 'quantity': qty,
                    'in_stock': c.item.current_stock, 'unit_cost': round(cost, 2), 'cost': round(cost * qty, 2),
                    'track_lots': c.item.track_lots, 'lots': _lots(c.item)})
    return out


def summary(appt):
    """Usage for API responses: the confirmed usage, or the pre-fill if not confirmed yet."""
    from inventory.models import StockMovement
    rec = active_record(appt)
    data = {'confirmed': bool(rec),
            'can_confirm': appt.status in CONFIRMABLE,
            'confirmed_by': _name(rec.confirmed_by) if rec else None,
            'confirmed_at': rec.created_at.isoformat() if rec else None,
            'note': rec.note if rec else ''}
    if rec:
        data['items'] = [{
            'item_id': l.item_id, 'item_name': l.item.name, 'unit': l.item.unit,
            'planned': l.planned, 'quantity': l.quantity, 'deducted': l.deducted, 'shortfall': l.shortfall,
            'lot_id': l.lot_id, 'lot_number': l.lot.lot_number if l.lot_id and l.lot else None,
            'unit_cost': round(float(l.unit_cost), 2), 'cost': round(float(l.unit_cost) * l.quantity, 2),
        } for l in rec.lines.select_related('item', 'lot')]
    else:
        data['items'] = prefill(appt)
    data['needs_confirmation'] = not rec and appt.status == 'completed' and bool(data['items'])
    manual = (StockMovement.objects.filter(appointment=appt, type__in=['used', 'wastage'])
              .exclude(note__startswith=AUTO).select_related('item', 'created_by'))
    data['manual_usage'] = [{'item_id': m.item_id, 'item_name': m.item.name, 'quantity': -m.quantity,
                             'type': m.type, 'by': _name(m.created_by)} for m in manual]
    data['total_cost'] = round(sum(i['cost'] for i in data['items']), 2)
    data['warnings'] = [f"{i['item_name']}: {i['shortfall']} {i['unit']} short"
                        for i in data['items'] if i.get('shortfall')]
    return data
