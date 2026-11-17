"""Lots, near-expiry alert and the inventory summary (dashboard KPIs)."""
import datetime

from django.db.models import F, Q, Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin
from .models import InventoryItem, Lot, PurchaseOrder, StockMovement
from .serializers import CATEGORY_MAP, CATEGORY_ID_MAP, serialize_lot

DEFAULT_EXPIRY_DAYS = 90


def _days_param(request, default=DEFAULT_EXPIRY_DAYS):
    raw = str(request.query_params.get('days', '') or '').strip()
    if not raw:
        return default, None
    if not raw.isdigit() or int(raw) > 3650:
        return None, Response({'days': 'Whole number of days between 0 and 3650.'}, status=400)
    return int(raw), None


class ItemLotsView(APIView):
    """
    GET /api/inventory/<id>/lots/?include_empty=true
    Lots of one item, earliest expiry first. `unassigned_quantity` is stock that isn't in any lot
    (e.g. stock that existed before track_lots was switched on).
    Any logged-in staff member — therapists need it to pick a lot when logging usage.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        item = InventoryItem.objects.filter(pk=pk).first()
        if not item:
            return Response({'error': 'Item not found.'}, status=404)
        lots = item.lots.select_related('supplier', 'item')
        if request.query_params.get('include_empty', '').lower() not in ('1', 'true'):
            lots = lots.filter(quantity_remaining__gt=0)
        today = timezone.localdate()
        data = [serialize_lot(l, today) for l in lots]
        in_lots = item.lots.aggregate(t=Sum('quantity_remaining'))['t'] or 0
        return Response({
            'inventory_item_id':   item.id,
            'item_name':           item.name,
            'track_lots':          item.track_lots,
            'current_stock':       item.current_stock,
            'quantity_in_lots':    in_lots,
            'unassigned_quantity': max(item.current_stock - in_lots, 0),
            'lots':                data,
        })


def near_expiry_lots(days):
    today = timezone.localdate()
    return (Lot.objects.select_related('item', 'supplier')
            .filter(item__track_lots=True, quantity_remaining__gt=0, expiry_date__isnull=False,
                    expiry_date__lte=today + datetime.timedelta(days=days))
            .order_by('expiry_date'))


class NearExpiryView(APIView):
    """
    GET /api/inventory/near-expiry/?days=90
    Lots (with stock left) that expire within N days — already-expired lots included and flagged.
    Also grouped per item for alert lists.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        days, error = _days_param(request)
        if error:
            return error
        today = timezone.localdate()
        lots = list(near_expiry_lots(days))
        rows = []
        for lot in lots:
            row = serialize_lot(lot, today)
            cost = lot.unit_cost if lot.unit_cost is not None else lot.item.cost_per_unit
            row.update({'unit': lot.item.unit, 'brand': lot.item.brand, 'sku': lot.item.sku,
                        'value': round(float(cost or 0) * lot.quantity_remaining, 2)})
            rows.append(row)
        items = {}
        for r in rows:
            it = items.setdefault(r['inventory_item_id'], {
                'inventory_item_id': r['inventory_item_id'], 'item_name': r['item_name'], 'unit': r['unit'],
                'quantity': 0, 'lots': 0, 'earliest_expiry': r['expiry_date'], 'has_expired': False,
            })
            it['quantity'] += r['quantity_remaining']
            it['lots'] += 1
            it['has_expired'] = it['has_expired'] or r['is_expired']
        return Response({
            'days':           days,
            'lot_count':      len(rows),
            'item_count':     len(items),
            'expired_count':  sum(1 for r in rows if r['is_expired']),
            'value_at_risk':  round(sum(r['value'] for r in rows), 2),
            'lots':           rows,
            'items':          list(items.values()),
        })


def _trend(current, previous):
    if previous == 0:
        pct = 100.0 if current > 0 else 0.0
        direction = 'up' if current > 0 else 'neutral'
    else:
        pct = round((current - previous) / previous * 100, 1)
        direction = 'up' if pct > 0 else ('down' if pct < 0 else 'neutral')
    return {'value': current, 'change_pct': abs(pct), 'trend': direction}


class InventorySummaryView(APIView):
    """
    GET /api/inventory/summary/?near_expiry_days=90
    Dashboard KPIs + stock value by category. Comparisons are with the stock on the 1st of this
    month, worked back from the movement log (at today's unit costs).
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        raw = str(request.query_params.get('near_expiry_days', '') or '').strip()
        if raw and not raw.isdigit():
            return Response({'near_expiry_days': 'Whole number of days.'}, status=400)
        days = int(raw) if raw else DEFAULT_EXPIRY_DAYS

        items = list(InventoryItem.objects.all())
        month_start = timezone.make_aware(datetime.datetime.combine(timezone.localdate().replace(day=1), datetime.time.min))
        since = dict(StockMovement.objects.filter(created_at__gte=month_start)
                     .values_list('item_id').annotate(t=Sum('quantity')).values_list('item_id', 't'))

        value = value_prev = 0.0
        units = units_prev = 0
        in_stock = in_stock_prev = low = low_prev = out = 0
        by_category = {}
        for i in items:
            cost = float(i.cost_per_unit or 0)
            prev_stock = max(i.current_stock - (since.get(i.id) or 0), 0)
            value += i.current_stock * cost
            value_prev += prev_stock * cost
            units += i.current_stock
            units_prev += prev_stock
            in_stock += i.current_stock > 0
            in_stock_prev += prev_stock > 0
            low += 0 < i.current_stock <= i.minimum_stock_alert
            low_prev += 0 < prev_stock <= i.minimum_stock_alert
            out += i.current_stock <= 0
            cat = by_category.setdefault(i.category or 'uncategorised', {'value': 0.0, 'items': 0, 'units': 0})
            cat['value'] += i.current_stock * cost
            cat['items'] += 1
            cat['units'] += i.current_stock

        pending = PurchaseOrder.objects.filter(status__in=['sent', 'partially_received']).prefetch_related('lines')
        pending_value = sum(float(l.unit_cost) * l.quantity_outstanding for po in pending for l in po.lines.all())
        lots = near_expiry_lots(days)
        today = timezone.localdate()

        categories = sorted([{
            'category': key,
            'category_id': CATEGORY_ID_MAP.get(key),
            'label': dict(InventoryItem.CATEGORY_CHOICES).get(key, 'Uncategorised'),
            'value': round(c['value'], 2),
            'pct': round(c['value'] / value * 100, 1) if value else 0.0,
            'items': c['items'],
            'units': c['units'],
        } for key, c in by_category.items()], key=lambda c: c['value'], reverse=True)

        return Response({
            'total_value':        _trend(round(value, 2), round(value_prev, 2)),
            'items_in_stock':     _trend(in_stock, in_stock_prev),
            'total_units':        _trend(units, units_prev),
            'low_stock_count':    _trend(low, low_prev),
            'out_of_stock_count': out,
            'item_count':         len(items),
            'near_expiry': {
                'days':      days,
                'lot_count': lots.count(),
                'expired':   lots.filter(expiry_date__lt=today).count(),
            },
            'pending_orders': {
                'count': pending.count(),
                'value': round(pending_value, 2),
            },
            'value_by_category': categories,
        })
