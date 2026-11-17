"""
Stock changes for inventory items. Every change goes through here so that the
item total, its lots (for items with track_lots) and the movement log stay in step.
Call these inside transaction.atomic() with the item row locked (select_for_update).
"""
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Lot, StockMovement


def parse_cost(value, field='unit_cost'):
    if value in (None, ''):
        return None
    try:
        cost = Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        raise ValidationError({field: 'Must be a number of 0 or more.'})
    if cost < 0:
        raise ValidationError({field: 'Must be a number of 0 or more.'})
    return cost


def parse_date(value, field):
    if value in (None, ''):
        return None
    import datetime
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        raise ValidationError({field: 'Use YYYY-MM-DD.'})


def lots_total(item):
    from django.db.models import Sum
    return item.lots.aggregate(t=Sum('quantity_remaining'))['t'] or 0


def receive_into_item(item, quantity, *, user=None, unit_cost=None, supplier=None, note='',
                      lot_number='', expiry_date=None, purchase_order=None):
    """
    Add stock to an item. For items with track_lots, the quantity goes into a lot:
    an existing lot with the same lot_number, or a new one. Returns (movement, lot).
    """
    lot_number = (lot_number or '').strip()[:80]
    if not item.track_lots and (lot_number or expiry_date):
        raise ValidationError({'lot_number': 'This item does not track lots. Set track_lots: true on the item first.'})

    lot = None
    if item.track_lots:
        if lot_number:
            lot = Lot.objects.select_for_update().filter(item=item, lot_number__iexact=lot_number).first()
        if lot is not None:
            if expiry_date and lot.expiry_date and lot.expiry_date != expiry_date:
                raise ValidationError({'expiry_date': f'Lot {lot.lot_number} already exists with expiry {lot.expiry_date}.'})
            lot.quantity_received += quantity
            lot.quantity_remaining += quantity
            lot.expiry_date = lot.expiry_date or expiry_date
            if unit_cost is not None:
                lot.unit_cost = unit_cost
            lot.supplier = lot.supplier or supplier
            lot.save()
        else:
            lot = Lot.objects.create(item=item, lot_number=lot_number, expiry_date=expiry_date,
                                     quantity_received=quantity, quantity_remaining=quantity,
                                     unit_cost=unit_cost, supplier=supplier or item.supplier)

    item.current_stock += quantity
    item.last_restock_date = timezone.localdate()
    if unit_cost is not None:
        item.cost_per_unit = unit_cost
    item.save()
    movement = StockMovement.objects.create(
        item=item, type='received', quantity=quantity, unit_cost=unit_cost,
        supplier=supplier or item.supplier, lot=lot, purchase_order=purchase_order,
        note=(note or '')[:255], created_by=user,
    )
    return movement, lot


def remove_from_item(item, quantity, movement_type, *, user=None, note='', lot=None):
    """
    Take stock out of an item. For items with track_lots, lots are used first-expiring-first
    (or the given lot first). Raises 400 if there isn't enough stock. Returns the movement.
    """
    if item.current_stock - quantity < 0:
        raise ValidationError({'quantity': f'Only {item.current_stock} {item.unit} in stock.'})
    used = []
    if item.track_lots:
        remaining = quantity
        if lot is not None:
            if lot.quantity_remaining < quantity:
                raise ValidationError({'lot_id': f'Lot {lot.lot_number or lot.id} only has {lot.quantity_remaining} left.'})
            ordered = [lot]
        else:
            ordered = list(Lot.objects.select_for_update().filter(item=item, quantity_remaining__gt=0)
                           .order_by('expiry_date', 'received_at'))
        for l in ordered:
            if remaining <= 0:
                break
            take = min(l.quantity_remaining, remaining)
            l.quantity_remaining -= take
            l.save(update_fields=['quantity_remaining', 'updated_at'])
            used.append((l, take))
            remaining -= take
        # anything left comes from stock that was never assigned to a lot
    item.current_stock -= quantity
    item.save()
    if len(used) > 1:
        note = (note + ' ' if note else '') + '[' + ', '.join(f'{l.lot_number or "lot " + str(l.id)}: {t}' for l, t in used) + ']'
    return StockMovement.objects.create(
        item=item, type=movement_type, quantity=-quantity, note=note[:255], created_by=user,
        lot=used[0][0] if len(used) == 1 else None,
    )


def add_correction(item, quantity, *, user=None, note='', lot=None):
    """Positive count correction. On lot items it goes into the given lot (or stays unassigned)."""
    if lot is not None:
        lot.quantity_remaining += quantity
        lot.save(update_fields=['quantity_remaining', 'updated_at'])
    item.current_stock += quantity
    item.save()
    return StockMovement.objects.create(item=item, type='correction', quantity=quantity, note=note[:255],
                                        created_by=user, lot=lot)
