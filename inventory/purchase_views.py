"""Purchase orders: draft → sent → partially_received → received (or cancelled)."""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from .models import InventoryItem, PurchaseOrder, PurchaseOrderLine, Supplier
from . import services
from .serializers import StockMovementSerializer, serialize_lot

FIRST_NUMBER = 1001
# Status changes allowed through PATCH {"status": …}
TRANSITIONS = {
    'draft': {'sent', 'cancelled'},
    'sent': {'cancelled'},
    'partially_received': {'cancelled'},   # closes the order; already-received stock stays
}


def _user_name(u):
    return (u.username or u.email.split('@')[0]) if u else None


def serialize_po(po, with_lines=True):
    lines = list(po.lines.select_related('item').all())
    total = sum(l.unit_cost * l.quantity_ordered for l in lines)
    received_value = sum(l.unit_cost * l.quantity_received for l in lines)
    data = {
        'id':               po.id,
        'number':           po.number,
        'supplier_id':      po.supplier_id,
        'supplier_name':    po.supplier.name,
        'status':           po.status,
        'status_label':     po.get_status_display(),
        'expected_date':    po.expected_date,
        'notes':            po.notes,
        'created_by':       po.created_by_id,
        'created_by_name':  _user_name(po.created_by),
        'created_at':       po.created_at,
        'sent_at':          po.sent_at,
        'received_at':      po.received_at,
        'line_count':       len(lines),
        'total':            float(round(total, 2)),
        'received_value':   float(round(received_value, 2)),
        'outstanding_value': float(round(total - received_value, 2)),
        'quantity_ordered':  sum(l.quantity_ordered for l in lines),
        'quantity_received': sum(l.quantity_received for l in lines),
    }
    if with_lines:
        data['lines'] = [{
            'id':                   l.id,
            'inventory_item_id':    l.item_id,
            'item_name':            l.item.name,
            'sku':                  l.item.sku,
            'unit':                 l.item.unit,
            'track_lots':           l.item.track_lots,
            'quantity_ordered':     l.quantity_ordered,
            'quantity_received':    l.quantity_received,
            'quantity_outstanding': l.quantity_outstanding,
            'unit_cost':            float(l.unit_cost),
            'line_total':           float(round(l.unit_cost * l.quantity_ordered, 2)),
        } for l in lines]
    return data


def _next_number():
    last = (PurchaseOrder.objects.filter(number__startswith='PO-')
            .order_by('-id').values_list('number', flat=True).first())
    try:
        n = int(last.split('-')[1]) + 1 if last else FIRST_NUMBER
    except (IndexError, ValueError):
        n = PurchaseOrder.objects.count() + FIRST_NUMBER
    return f'PO-{n}'


def _int(value, field, minimum=1):
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValidationError({field: f'Whole number of {minimum} or more.'})
    if value < minimum:
        raise ValidationError({field: f'Whole number of {minimum} or more.'})
    return value


def _replace_lines(po, lines):
    if not isinstance(lines, list) or not lines:
        raise ValidationError({'lines': 'At least one line: [{inventory_item_id, quantity_ordered, unit_cost}].'})
    po.lines.all().delete()
    for i, line in enumerate(lines):
        item = InventoryItem.objects.filter(pk=line.get('inventory_item_id')).first()
        if not item:
            raise ValidationError({f'lines[{i}].inventory_item_id': 'Inventory item not found.'})
        cost = services.parse_cost(line.get('unit_cost'), f'lines[{i}].unit_cost')
        PurchaseOrderLine.objects.create(
            order=po, item=item,
            quantity_ordered=_int(line.get('quantity_ordered'), f'lines[{i}].quantity_ordered'),
            unit_cost=cost if cost is not None else item.cost_per_unit,
        )


def _supplier(value):
    s = Supplier.objects.filter(pk=value, is_active=True).first() if str(value or '').isdigit() else None
    if not s:
        raise ValidationError({'supplier_id': 'Active supplier not found.'})
    return s


def _get_po(pk):
    return PurchaseOrder.objects.select_related('supplier', 'created_by').filter(pk=pk).first()


class PurchaseOrderListView(APIView):
    """
    GET  /api/purchase-orders/?status=sent&supplier_id=3&search=PO-10&date_from=2026-01-01&date_to=2026-12-31&page=1&page_size=20
         status can be a comma list, e.g. status=sent,partially_received (open orders)
         date_from / date_to filter by the order's creation date (both days included)
    POST /api/purchase-orders/
         {supplier_id, expected_date?, notes?, lines: [{inventory_item_id, quantity_ordered, unit_cost?}]}
         Creates a draft. unit_cost defaults to the item's cost_per_unit.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        p = request.query_params
        qs = PurchaseOrder.objects.select_related('supplier', 'created_by').prefetch_related('lines__item')
        if p.get('status'):
            qs = qs.filter(status__in=[s.strip() for s in p['status'].split(',') if s.strip()])
        if str(p.get('supplier_id', '')).isdigit():
            qs = qs.filter(supplier_id=int(p['supplier_id']))
        if p.get('search'):
            qs = qs.filter(Q(number__icontains=p['search']) | Q(supplier__name__icontains=p['search']))
        import datetime as dt
        for field in ('date_from', 'date_to'):
            if p.get(field):
                try:
                    d = dt.date.fromisoformat(p[field])
                except ValueError:
                    return Response({field: 'Use YYYY-MM-DD.'}, status=400)
                if field == 'date_to':
                    d += dt.timedelta(days=1)
                start = timezone.make_aware(dt.datetime.combine(d, dt.time.min))
                qs = qs.filter(created_at__gte=start) if field == 'date_from' else qs.filter(created_at__lt=start)
        if 'page' in p or 'page_size' in p:
            from django.core.paginator import Paginator
            try:
                size = max(1, min(int(p.get('page_size') or 20), 100))
                num = int(p.get('page') or 1)
            except ValueError:
                return Response({'page': 'page and page_size must be whole numbers.'}, status=400)
            paginator = Paginator(qs, size)
            page = paginator.get_page(num)
            return Response({'count': paginator.count, 'page': page.number, 'page_size': size,
                             'total_pages': paginator.num_pages,
                             'results': [serialize_po(po, with_lines=False) for po in page.object_list]})
        return Response([serialize_po(po, with_lines=False) for po in qs])

    def post(self, request):
        supplier = _supplier(request.data.get('supplier_id'))
        expected = services.parse_date(request.data.get('expected_date'), 'expected_date')
        for attempt in range(3):
            try:
                with transaction.atomic():
                    po = PurchaseOrder.objects.create(
                        number=_next_number(), supplier=supplier, expected_date=expected,
                        notes=str(request.data.get('notes', '') or ''), created_by=request.user,
                    )
                    _replace_lines(po, request.data.get('lines'))
                break
            except IntegrityError:          # two orders created at the same moment
                if attempt == 2:
                    raise
        return Response(serialize_po(_get_po(po.pk)), status=201)


class PurchaseOrderDetailView(APIView):
    """
    GET   /api/purchase-orders/<id>/
    PATCH /api/purchase-orders/<id>/
          {expected_date?, notes?}                 — any open order
          {supplier_id?, lines?}                   — drafts only (lines are replaced as a whole)
          {status: "sent" | "cancelled"}           — draft→sent, draft/sent/partially_received→cancelled
          Receiving changes the status automatically (see /receive/).
    """
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        po = _get_po(pk)
        if not po:
            return Response({'error': 'Purchase order not found.'}, status=404)
        data = serialize_po(po)
        data['receipts'] = StockMovementSerializer(
            po.movements.select_related('item', 'supplier', 'lot', 'created_by', 'purchase_order'), many=True).data
        return Response(data)

    def patch(self, request, pk):
        with transaction.atomic():
            po = PurchaseOrder.objects.select_for_update().filter(pk=pk).first()
            if not po:
                return Response({'error': 'Purchase order not found.'}, status=404)
            if po.status in ('received', 'cancelled'):
                return Response({'error': f'This order is {po.status} and can no longer be changed.'}, status=400)
            d = request.data
            if ('lines' in d or 'supplier_id' in d) and po.status != 'draft':
                return Response({'error': 'Supplier and lines can only be changed while the order is a draft.'}, status=400)
            if 'supplier_id' in d:
                po.supplier = _supplier(d['supplier_id'])
            if 'lines' in d:
                _replace_lines(po, d['lines'])
            if 'expected_date' in d:
                po.expected_date = services.parse_date(d['expected_date'], 'expected_date')
            if 'notes' in d:
                po.notes = str(d['notes'] or '')
            if 'status' in d and d['status'] != po.status:
                new = d['status']
                if new not in TRANSITIONS.get(po.status, set()):
                    allowed = ', '.join(sorted(TRANSITIONS.get(po.status, set()))) or 'none'
                    return Response({'status': f'Cannot change {po.status} → {new}. Allowed: {allowed}. '
                                               f'Use /receive/ to receive stock.'}, status=400)
                if new == 'sent':
                    if not po.lines.exists():
                        return Response({'status': 'Add at least one line before sending.'}, status=400)
                    po.sent_at = timezone.now()
                po.status = new
            po.save()
        return Response(serialize_po(_get_po(pk)))


class PurchaseOrderReceiveView(APIView):
    """
    POST /api/purchase-orders/<id>/receive/
    {
      "lines": [{"line_id": 12, "quantity": 5, "lot_number": "L2611", "expiry_date": "2027-06-30", "unit_cost": 12.5}],
      "note": "Delivery note 8812"
    }
    Partial receipts allowed. Each line adds stock (into a lot for lot-tracked items), logs a
    'received' movement linked to the order, and the order becomes partially_received / received.
    unit_cost defaults to the line's cost. Instead of line_id you can send inventory_item_id.
    """
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        entries = request.data.get('lines')
        if not isinstance(entries, list) or not entries:
            return Response({'lines': 'Send [{line_id, quantity, lot_number?, expiry_date?, unit_cost?}].'}, status=400)
        note = str(request.data.get('note', '') or '')
        results = []
        with transaction.atomic():
            po = PurchaseOrder.objects.select_for_update().select_related('supplier').filter(pk=pk).first()
            if not po:
                return Response({'error': 'Purchase order not found.'}, status=404)
            if po.status not in ('sent', 'partially_received'):
                return Response({'error': f'Only sent orders can be received (this one is {po.status}).'}, status=400)
            for i, e in enumerate(entries):
                line_q = po.lines.select_for_update()
                if e.get('line_id') not in (None, ''):
                    line = line_q.filter(pk=e['line_id']).first()
                else:
                    line = line_q.filter(item_id=e.get('inventory_item_id')).first()
                if not line:
                    raise ValidationError({f'lines[{i}]': 'Line not found on this order.'})
                qty = _int(e.get('quantity'), f'lines[{i}].quantity')
                if qty > line.quantity_outstanding:
                    raise ValidationError({f'lines[{i}].quantity': f'Only {line.quantity_outstanding} outstanding on this line.'})
                cost = services.parse_cost(e.get('unit_cost'), f'lines[{i}].unit_cost')
                item = InventoryItem.objects.select_for_update().get(pk=line.item_id)
                movement, lot = services.receive_into_item(
                    item, qty, user=request.user, unit_cost=cost if cost is not None else line.unit_cost,
                    supplier=po.supplier, note=f'{po.number}' + (f' — {note}' if note else ''),
                    lot_number=str(e.get('lot_number', '') or ''),
                    expiry_date=services.parse_date(e.get('expiry_date'), f'lines[{i}].expiry_date'),
                    purchase_order=po,
                )
                line.quantity_received += qty
                line.save(update_fields=['quantity_received'])
                results.append({'line_id': line.id, 'inventory_item_id': item.id, 'quantity': qty,
                                'current_stock': item.current_stock,
                                'movement': StockMovementSerializer(movement).data,
                                'lot': serialize_lot(lot) if lot else None})
            all_lines = list(po.lines.all())
            if all(l.quantity_outstanding == 0 for l in all_lines):
                po.status, po.received_at = 'received', timezone.now()
            else:
                po.status = 'partially_received'
            po.save()
        data = serialize_po(_get_po(pk))
        data['received'] = results
        return Response(data, status=201)
