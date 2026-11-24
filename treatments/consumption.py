"""
Stock used by treatments.

When an appointment becomes `completed`, each consumable of its treatment is taken from stock
(earliest-expiring lot first, logged as a 'used' movement linked to the appointment, by the
appointment's therapist). Rules agreed with the clinic:

- Not enough stock → the appointment still completes; whatever is in stock is deducted, the rest is
  recorded as a shortfall and admins get a `stock_shortfall` notification.
- Items the therapist already logged by hand for this appointment are skipped (no double count).
- Runs once per completion. If the appointment is moved out of `completed`, the stock is put back
  and the rows are marked reversed; completing again deducts again.
"""
import logging

from django.db import transaction
from django.db.models import Sum

log = logging.getLogger('aura.consumption')


def _name(u):
    return (u.username or u.email.split('@')[0]) if u else None


def active_rows(appt):
    from .models import AppointmentConsumption
    return AppointmentConsumption.objects.filter(appointment=appt, reversed=False)


AUTO = 'Auto: '


def _take(item, quantity, appt, note):
    """
    Deduct `quantity`. Lot items get one movement per lot (earliest expiry first) so each can be put
    back into its own lot later. Returns the first movement.
    """
    from inventory.models import Lot
    from inventory.services import remove_from_item
    first, left = None, quantity
    if item.track_lots:
        for lot in Lot.objects.select_for_update().filter(item=item, quantity_remaining__gt=0).order_by('expiry_date', 'received_at'):
            if left <= 0:
                break
            n = min(lot.quantity_remaining, left)
            m = remove_from_item(item, n, 'used', user=appt.staff, note=note, lot=lot, appointment=appt)
            first, left = first or m, left - n
    if left > 0:      # plain items, or lot items' stock that isn't in any lot
        m = remove_from_item(item, left, 'used', user=appt.staff, note=note, appointment=appt)
        first = first or m
    return first


def consume_for_appointment(appt):
    from inventory.models import InventoryItem, StockMovement
    from .models import AppointmentConsumption, TreatmentConsumable

    if appt.status != 'completed' or not appt.treatment_id or active_rows(appt).exists():
        return []
    links = list(TreatmentConsumable.objects.filter(treatment_id=appt.treatment_id).select_related('item'))
    if not links:
        return []
    rows, short = [], []
    treatment_name = appt.treatment.name if appt.treatment else 'treatment'
    with transaction.atomic():
        for link in links:
            item = InventoryItem.objects.select_for_update().get(pk=link.item_id)
            manual = -(StockMovement.objects.filter(appointment=appt, item=item, type='used')
                       .exclude(note__startswith=AUTO).aggregate(t=Sum('quantity'))['t'] or 0)
            row = AppointmentConsumption(appointment=appt, item=item, planned=link.quantity,
                                         unit_cost=item.cost_per_unit or 0)
            if manual > 0:
                row.skipped_manual = True
            else:
                take = min(link.quantity, max(item.current_stock, 0))
                if take > 0:
                    row.movement = _take(item, take, appt, f'{AUTO}{treatment_name} (appointment #{appt.id})')
                    row.deducted = take
                row.shortfall = link.quantity - take
                if row.shortfall:
                    short.append((item, row.shortfall))
            row.save()
            rows.append(row)
    if short:
        _notify_shortfall(appt, short)
    return rows


def reverse_for_appointment(appt):
    from inventory.models import InventoryItem, Lot, StockMovement
    from inventory.services import add_correction
    rows = list(active_rows(appt))
    if not rows:
        return
    note = f'Returned: appointment #{appt.id} is no longer completed'
    with transaction.atomic():
        for row in rows:
            if row.deducted > 0:
                item = InventoryItem.objects.select_for_update().get(pk=row.item_id)
                # the movements this row made (one per lot); fall back to a single unassigned return
                moves = list(StockMovement.objects.filter(
                    appointment=appt, item_id=row.item_id, type='used', note__startswith=AUTO,
                    id__gte=row.movement_id or 0).select_related('lot').order_by('id')) if row.movement_id else []
                left = row.deducted
                for m in moves:
                    n = min(-m.quantity, left)
                    if n <= 0:
                        break
                    lot = Lot.objects.select_for_update().get(pk=m.lot_id) if m.lot_id else None
                    rev = add_correction(item, n, user=appt.staff, lot=lot, appointment=appt, note=note)
                    row.reversal_movement = row.reversal_movement or rev
                    left -= n
                if left > 0:
                    rev = add_correction(item, left, user=appt.staff, appointment=appt, note=note)
                    row.reversal_movement = row.reversal_movement or rev
            row.reversed = True
            row.save(update_fields=['reversed', 'reversal_movement'])


def appointment_saved(appt):
    """post_save hook: deduct on completion, put back if un-completed."""
    if appt.status == 'completed':
        consume_for_appointment(appt)
    elif active_rows(appt).exists():
        reverse_for_appointment(appt)


def _notify_shortfall(appt, short):
    from notifications import service as notify
    patient = appt.patient.name if appt.patient_id and appt.patient else 'a patient'
    treatment = appt.treatment.name if appt.treatment_id and appt.treatment else 'treatment'
    parts = ', '.join(f'{item.name} ({qty} {item.unit} short)' for item, qty in short)
    notify.notify(notify.clinic_admins(appt.clinic_id), 'stock_shortfall',
                  f'Not enough stock for {patient}\'s {treatment}: {parts}. Please check the inventory.',
                  {'appointment_id': appt.id, 'item_ids': [item.id for item, _ in short]}, actor=None)


def summary(appt):
    """What the appointment used / should use — for API responses."""
    from inventory.models import StockMovement
    from .models import TreatmentConsumable
    rows = list(active_rows(appt).select_related('item'))
    data = {
        'deducted': bool(rows),
        'items': [{
            'item_id': r.item_id, 'item_name': r.item.name, 'unit': r.item.unit,
            'planned': r.planned, 'deducted': r.deducted, 'shortfall': r.shortfall,
            'skipped_manual': r.skipped_manual,
            'unit_cost': round(float(r.unit_cost), 2), 'cost': round(float(r.unit_cost) * r.deducted, 2),
        } for r in rows],
    }
    if not rows and appt.treatment_id:       # not completed yet: show what it will use
        data['items'] = [{
            'item_id': c.item_id, 'item_name': c.item.name, 'unit': c.item.unit, 'planned': c.quantity,
            'deducted': 0, 'shortfall': 0, 'skipped_manual': False,
            'unit_cost': round(float(c.item.cost_per_unit or 0), 2),
            'cost': round(float(c.item.cost_per_unit or 0) * c.quantity, 2),
            'in_stock': c.item.current_stock,
        } for c in TreatmentConsumable.objects.filter(treatment_id=appt.treatment_id).select_related('item')]
    manual = (StockMovement.objects.filter(appointment=appt, type__in=['used', 'wastage'])
              .exclude(note__startswith=AUTO).select_related('item', 'created_by'))
    data['manual_usage'] = [{'item_id': m.item_id, 'item_name': m.item.name, 'quantity': -m.quantity,
                             'type': m.type, 'by': _name(m.created_by)} for m in manual]
    data['total_cost'] = round(sum(i['cost'] for i in data['items']), 2)
    data['warnings'] = [f"{i['item_name']}: {i['shortfall']} {i['unit']} short" for i in data['items'] if i['shortfall']]
    return data
