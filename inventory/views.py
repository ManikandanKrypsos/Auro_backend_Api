import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin
from .models import InventoryItem, StockMovement, Supplier, Lot
from . import services
from .serializers import (
    InventoryItemSerializer, InventoryItemListSerializer,
    InventoryItemWriteSerializer, StockMovementSerializer,
    StockMovementWriteSerializer, serialize_supplier, serialize_lot,
)


class InventoryMetaView(APIView):
    """
    GET /api/inventory/meta/  — all dropdown options with IDs
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            'categories': [
                {'id': 1, 'value': 'consumable', 'label': 'Consumable'},
                {'id': 2, 'value': 'equipment',  'label': 'Equipment'},
                {'id': 3, 'value': 'product',    'label': 'Product'},
                {'id': 4, 'value': 'disposable', 'label': 'Disposable'},
            ],
            'units': [
                {'id': 1, 'value': 'ml',    'label': 'ml'},
                {'id': 2, 'value': 'pcs',   'label': 'pcs'},
                {'id': 3, 'value': 'units', 'label': 'units'},
                {'id': 4, 'value': 'kg',    'label': 'kg'},
                {'id': 5, 'value': 'g',     'label': 'g'},
                {'id': 6, 'value': 'l',     'label': 'l'},
            ],
            'movement_types': [
                {'value': 'added',    'label': 'Added to Inventory'},
                {'value': 'used',     'label': 'Used in Treatment'},
                {'value': 'adjusted', 'label': 'Manual Adjustment'},
                {'value': 'ordered',  'label': 'Order More'},
                {'value': 'received', 'label': 'Received'},
                {'value': 'wastage',  'label': 'Wastage'},
                {'value': 'correction', 'label': 'Count Correction'},
                {'value': 'returned', 'label': 'Returned to Supplier'},
            ],
            'adjust_reasons': [
                {'value': 'used',             'label': 'Used in treatment'},
                {'value': 'wastage',          'label': 'Wastage (lost / damaged / expired)'},
                {'value': 'returned',         'label': 'Returned to supplier'},
                {'value': 'count_correction', 'label': 'Count correction'},
            ],
        })


class InventoryListView(APIView):
    """
    GET  /api/inventory/           — list items
         ?search=                  name, SKU, brand or supplier
         ?category=consumable      (or ?category_id=1)
         ?brand=Restylane
         ?supplier_id=3
         ?status=in_stock|low_stock|out_of_stock
         ?low_stock=true           same as status=low_stock (kept for older screens)
         ?track_lots=true|false
         ?page=1&page_size=20      optional pagination (max 100) → {count, page, page_size, total_pages, results}

    POST /api/inventory/           — add new item (admin only)
    """
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        from django.db.models import F, Q, Min
        from .serializers import CATEGORY_MAP
        p = request.query_params
        items = InventoryItem.objects.select_related('supplier').annotate(
            next_expiry=Min('lots__expiry_date', filter=Q(lots__quantity_remaining__gt=0))).order_by('name', 'id')

        search = p.get('search', '').strip()
        if search:
            items = items.filter(Q(name__icontains=search) | Q(sku__icontains=search) |
                                 Q(brand__icontains=search) | Q(supplier__name__icontains=search) |
                                 Q(supplier_name__icontains=search))
        if p.get('category'):
            items = items.filter(category=p['category'].strip())
        if p.get('category_id', '').isdigit():
            items = items.filter(category=CATEGORY_MAP.get(int(p['category_id']), ''))
        if p.get('brand'):
            items = items.filter(brand__iexact=p['brand'].strip())
        if p.get('supplier_id', '').isdigit():
            items = items.filter(supplier_id=int(p['supplier_id']))
        status = p.get('status', '').strip()
        if not status and p.get('low_stock') == 'true':      # older screens: low or zero, as before
            items = items.filter(current_stock__lte=F('minimum_stock_alert'))
        if status == 'out_of_stock':
            items = items.filter(current_stock__lte=0)
        elif status == 'low_stock':
            items = items.filter(current_stock__gt=0, current_stock__lte=F('minimum_stock_alert'))
        elif status == 'in_stock':
            items = items.filter(current_stock__gt=F('minimum_stock_alert'))
        if p.get('track_lots') in ('true', 'false'):
            items = items.filter(track_lots=p['track_lots'] == 'true')

        if 'page' in p or 'page_size' in p:
            from django.core.paginator import Paginator
            try:
                page_size = max(1, min(int(p.get('page_size') or 20), 100))
                page_num = int(p.get('page') or 1)
            except ValueError:
                return Response({'page': 'page and page_size must be whole numbers.'}, status=400)
            paginator = Paginator(items, page_size)
            page = paginator.get_page(page_num)
            return Response({
                'count': paginator.count, 'page': page.number, 'page_size': page_size,
                'total_pages': paginator.num_pages,
                'results': InventoryItemListSerializer(page.object_list, many=True).data,
            })
        return Response(InventoryItemListSerializer(items, many=True).data)

    def post(self, request):
        serializer = InventoryItemWriteSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            item = serializer.save()
            return Response(InventoryItemSerializer(item).data, status=201)
        return Response(serializer.errors, status=400)


class InventoryDetailView(APIView):
    """
    GET    /api/inventory/<id>/    — get item detail with stock movements
    PATCH  /api/inventory/<id>/    — update item
    DELETE /api/inventory/<id>/    — delete item
    """
    permission_classes = [IsAdmin]

    def _get_item(self, pk):
        try:
            return InventoryItem.objects.prefetch_related('movements').get(pk=pk)
        except InventoryItem.DoesNotExist:
            return None

    def get(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=404)
        return Response(InventoryItemSerializer(item).data)

    def patch(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=404)
        serializer = InventoryItemWriteSerializer(item, data=request.data, partial=True, context={'user': request.user})
        if serializer.is_valid():
            item = serializer.save()
            return Response(InventoryItemSerializer(item).data)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=404)
        item.delete()
        return Response({'message': 'Item deleted successfully.'})


class OutOfStockView(APIView):
    """
    GET /api/inventory/out-of-stock/
    Returns items where current_stock = 0 or current_stock <= minimum_stock_alert.

    ?type=zero        — only completely out of stock (current_stock = 0)
    ?type=low         — only low stock (current_stock <= minimum_stock_alert)
    Default           — both zero and low stock combined
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        from django.db.models import F
        stock_type = request.query_params.get('type', '').strip()

        if stock_type == 'zero':
            items = InventoryItem.objects.filter(current_stock=0)
        elif stock_type == 'low':
            items = InventoryItem.objects.filter(
                current_stock__gt=0,
                current_stock__lte=F('minimum_stock_alert')
            )
        else:
            items = InventoryItem.objects.filter(
                current_stock__lte=F('minimum_stock_alert')
            )

        return Response(InventoryItemListSerializer(items, many=True).data)


class StockCountView(APIView):
    """
    GET /api/inventory/stock-count/
    Returns count of low stock and zero stock items.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        from django.db.models import F
        zero_count  = InventoryItem.objects.filter(current_stock=0).count()
        low_count   = InventoryItem.objects.filter(
            current_stock__gt=0,
            current_stock__lte=F('minimum_stock_alert')
        ).count()
        total_stock = InventoryItem.objects.count()
        return Response({
            'low_stock_count':       low_count,
            'zero_stock_count':      zero_count,
            'total_low_zero_count':  zero_count + low_count,
            'total_stock':           total_stock,
        })


class StockMovementListView(APIView):
    """
    GET  /api/inventory/<id>/movements/     — list all movements for an item
    POST /api/inventory/<id>/movements/     — add a stock movement (restock, used, adjust)

    POST body:
    {
        "type":     "added",
        "quantity": 20,
        "note":     "Restocked from supplier"
    }
    """
    permission_classes = [IsAdmin]

    def _get_item(self, pk):
        try:
            return InventoryItem.objects.get(pk=pk)
        except InventoryItem.DoesNotExist:
            return None

    def get(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=404)
        movements = list(StockMovement.objects.filter(item=item).select_related('supplier', 'created_by', 'lot', 'purchase_order', 'appointment__patient', 'appointment__treatment', 'appointment__staff'))
        data = StockMovementSerializer(movements, many=True).data
        # Stock level right after each movement (newest first), worked back from the current stock
        balance = item.current_stock
        for row, m in zip(data, movements):
            row['balance_after'] = balance
            balance -= m.quantity
        return Response(data)

    def post(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=404)

        serializer = StockMovementWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        v        = serializer.validated_data
        quantity = v['quantity']
        mtype    = v['type']
        note     = v.get('note', '')

        with transaction.atomic():
            item = _locked_item(pk)
            if item.current_stock + quantity < 0:
                return Response({'error': f'Insufficient stock. Current stock is {item.current_stock}.'}, status=400)
            if quantity < 0:
                movement = services.remove_from_item(item, -quantity, mtype, user=request.user, note=note)
            else:
                item.current_stock += quantity
                if mtype in ['added', 'ordered']:
                    item.last_restock_date = datetime.date.today()
                item.save()
                movement = StockMovement.objects.create(item=item, type=mtype, quantity=quantity, note=note,
                                                        created_by=request.user)

        return Response({
            'message':       'Stock updated successfully.',
            'current_stock': item.current_stock,
            'movement':      StockMovementSerializer(movement).data,
        }, status=201)


# ── Receive / adjust stock (every change is logged as a movement) ─────────────

def _locked_item(pk):
    return InventoryItem.objects.select_for_update().filter(pk=pk).first()


def _movement_response(item, movement, message, status=201):
    return Response({
        'message':       message,
        'item_id':       item.id,
        'current_stock': item.current_stock,
        'is_low_stock':  item.is_low_stock,
        'movement':      StockMovementSerializer(movement).data,
    }, status=status)


class ReceiveStockView(APIView):
    """
    POST /api/inventory/<id>/receive/
    Body: {"quantity": 10, "unit_cost": 12.50, "supplier_id": 3, "note": "Invoice 4411",
           "lot_number": "L2611-A", "expiry_date": "2027-06-30"}
    quantity is required (whole number > 0); the rest is optional.
    lot_number / expiry_date: only for items with track_lots — the quantity goes into that lot
    (an existing lot with the same number is topped up, otherwise a new lot is created).
    Adds stock, sets last_restock_date, updates the item's cost_per_unit when unit_cost is sent,
    and logs a 'received' movement.
    """
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        errors = {}
        try:
            quantity = int(request.data.get('quantity'))
            if quantity <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors['quantity'] = 'A whole number greater than 0 is required.'
            quantity = None
        unit_cost = expiry_date = None
        try:
            unit_cost = services.parse_cost(request.data.get('unit_cost'))
        except ValidationError as e:
            errors.update({k: v for k, v in e.detail.items()})
        try:
            expiry_date = services.parse_date(request.data.get('expiry_date'), 'expiry_date')
        except ValidationError as e:
            errors.update({k: v for k, v in e.detail.items()})
        supplier = None
        if request.data.get('supplier_id') not in (None, ''):
            supplier = Supplier.objects.filter(pk=request.data['supplier_id'], is_active=True).first()
            if not supplier:
                errors['supplier_id'] = 'Supplier not found.'
        if errors:
            return Response({k: (str(v[0]) if isinstance(v, list) else str(v)) for k, v in errors.items()}, status=400)

        with transaction.atomic():
            item = _locked_item(pk)
            if not item:
                return Response({'error': 'Item not found.'}, status=404)
            movement, lot = services.receive_into_item(
                item, quantity, user=request.user, unit_cost=unit_cost, supplier=supplier,
                note=str(request.data.get('note', '')), lot_number=str(request.data.get('lot_number', '') or ''),
                expiry_date=expiry_date,
            )
        response = _movement_response(item, movement, f'Received {quantity} {item.unit}.')
        response.data['lot'] = serialize_lot(lot) if lot else None
        return response


class AdjustStockView(APIView):
    """
    POST /api/inventory/<id>/adjust/
    Body: {"quantity_delta": -2, "reason": "used" | "wastage" | "count_correction",
           "note": "Broken vial", "lot_id": 7, "appointment_id": 501}
    quantity_delta is a non-zero whole number (negative removes stock, positive adds).
    "used" (product used in a treatment) and "wastage" must be negative. Stock can't go below zero.
    appointment_id (optional, any reason): links the movement to the appointment it came from.

    Who can call it:
      reason "used"                       — admin, reception, therapist
                                            (therapists: appointment_id is required and must be their own)
      reason "wastage" / "returned" (to supplier) / "count_correction" — admin only
    The movement's created_by is whoever made the call, so usage is attributed to the therapist.
    lot_id (optional, lot-tracked items): which lot it applies to. Without it, removals use the
    earliest-expiring lots first and additions stay unassigned to a lot.
    """
    permission_classes = [IsAuthenticated]
    STAFF_ROLES = ('admin', 'reception', 'therapist')
    REASON_TO_TYPE = {'used': 'used', 'wastage': 'wastage', 'count_correction': 'correction', 'returned': 'returned'}
    MUST_BE_NEGATIVE = {'used': 'Product usage', 'wastage': 'Wastage', 'returned': 'A return to the supplier'}

    def post(self, request, pk):
        role = getattr(request.user, 'role', '') or ''
        reason = request.data.get('reason')
        if role not in self.STAFF_ROLES:
            return Response({'error': 'You do not have permission to adjust stock.'}, status=403)
        if role != 'admin' and reason != 'used':
            return Response({'error': 'Only an admin can record wastage, returns or count corrections.', 'code': 'admin_only'}, status=403)

        errors = {}
        try:
            delta = int(request.data.get('quantity_delta'))
            if delta == 0:
                raise ValueError
        except (TypeError, ValueError):
            errors['quantity_delta'] = 'A non-zero whole number is required (negative removes stock).'
            delta = None
        if reason not in self.REASON_TO_TYPE:
            errors['reason'] = 'Use "used", "wastage", "returned" or "count_correction".'
        elif reason in self.MUST_BE_NEGATIVE and delta is not None and delta > 0:
            errors['quantity_delta'] = f'{self.MUST_BE_NEGATIVE[reason]} removes stock, so quantity_delta must be negative.'
        appointment = None
        if request.data.get('appointment_id') not in (None, ''):
            from appointments.models import Appointment
            appointment = Appointment.objects.filter(pk=str(request.data['appointment_id'])).first() \
                if str(request.data['appointment_id']).isdigit() else None
            if not appointment:
                errors['appointment_id'] = 'Appointment not found.'
            elif appointment.status == 'cancelled':
                errors['appointment_id'] = 'This appointment is cancelled.'
        if role == 'therapist':
            if 'appointment_id' not in errors and not appointment:
                errors['appointment_id'] = 'Therapists must link product usage to their appointment.'
            elif appointment and appointment.staff_id != request.user.pk:
                return Response({'error': 'You can only record usage on your own appointments.', 'code': 'not_own_appointment'}, status=403)
        if errors:
            return Response(errors, status=400)

        with transaction.atomic():
            item = _locked_item(pk)
            if not item:
                return Response({'error': 'Item not found.'}, status=404)
            if item.current_stock + delta < 0:
                return Response({'quantity_delta': f'Only {item.current_stock} {item.unit} in stock.'}, status=400)
            lot = None
            if request.data.get('lot_id') not in (None, ''):
                lot = Lot.objects.select_for_update().filter(pk=request.data['lot_id'], item=item).first()
                if not lot:
                    return Response({'lot_id': 'Lot not found for this item.'}, status=400)
            note = str(request.data.get('note', ''))
            if delta < 0:
                movement = services.remove_from_item(item, -delta, self.REASON_TO_TYPE[reason],
                                                     user=request.user, note=note, lot=lot, appointment=appointment)
            else:
                movement = services.add_correction(item, delta, user=request.user, note=note, lot=lot,
                                                   appointment=appointment)
        return _movement_response(item, movement, 'Stock adjusted.')


def _filtered_movements(request, require_dates=False):
    """
    Shared by the movements list and its summary: role scoping + filters.
    Returns (queryset, date_from, date_to, error_response).
    Admin / reception: everyone (optional created_by_id). Therapists: only their own movements.
    """
    import datetime as dt
    p = request.query_params
    qs = StockMovement.objects.all()
    role = getattr(request.user, 'role', '') or ''
    if role not in ('admin', 'reception', 'therapist'):
        return None, None, None, Response({'error': 'You do not have permission to view stock movements.'}, status=403)
    if role == 'therapist':
        if p.get('created_by_id') and str(p['created_by_id']) != str(request.user.pk):
            return None, None, None, Response({'error': 'Therapists can only see their own movements.', 'code': 'not_own_records'}, status=403)
        qs = qs.filter(created_by=request.user)
    for field in ('appointment_id', 'item_id', 'created_by_id'):
        if p.get(field):
            if not str(p[field]).isdigit():
                return None, None, None, Response({field: 'Must be a whole number.'}, status=400)
            qs = qs.filter(**{field: int(p[field])})
    if p.get('type'):
        qs = qs.filter(type__in=[t.strip() for t in p['type'].split(',') if t.strip()])
    dates = {}
    for field in ('date_from', 'date_to'):
        if not p.get(field):
            if require_dates:
                return None, None, None, Response({field: 'This parameter is required (YYYY-MM-DD).'}, status=400)
            dates[field] = None
            continue
        try:
            dates[field] = dt.date.fromisoformat(p[field])
        except ValueError:
            return None, None, None, Response({field: 'Use YYYY-MM-DD.'}, status=400)
    if dates['date_from'] and dates['date_to'] and dates['date_from'] > dates['date_to']:
        return None, None, None, Response({'date_to': 'date_to must be on or after date_from.'}, status=400)
    if dates['date_from']:
        qs = qs.filter(created_at__gte=timezone.make_aware(dt.datetime.combine(dates['date_from'], dt.time.min)))
    if dates['date_to']:
        qs = qs.filter(created_at__lt=timezone.make_aware(
            dt.datetime.combine(dates['date_to'] + dt.timedelta(days=1), dt.time.min)))
    return qs, dates['date_from'], dates['date_to'], None


class MovementSearchView(APIView):
    """
    GET /api/inventory/movements/?appointment_id=501&item_id=&type=used&created_by_id=8&date_from=2026-11-01&date_to=2026-11-30
    Stock movements across all items, newest first — e.g. everything used in one appointment,
    or one therapist's usage history. Optional pagination with page / page_size (max 100).
    Admin / reception: all movements. Therapists: only movements they made themselves.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        p = request.query_params
        qs, _, _, error = _filtered_movements(request)
        if error:
            return error
        qs = qs.select_related('item', 'supplier', 'created_by', 'lot', 'purchase_order',
                               'appointment__patient', 'appointment__treatment', 'appointment__staff')

        def rows(movs):
            out = []
            for m in movs:
                row = StockMovementSerializer(m).data
                row.update({'item_id': m.item_id, 'item_name': m.item.name, 'unit': m.item.unit,
                            'cost': round(abs(m.quantity) * float(m.unit_cost if m.unit_cost is not None else m.item.cost_per_unit or 0), 2)})
                out.append(row)
            return out

        if 'page' in p or 'page_size' in p:
            from django.core.paginator import Paginator
            try:
                size = max(1, min(int(p.get('page_size') or 20), 100))
                num = int(p.get('page') or 1)
            except ValueError:
                return Response({'page': 'page and page_size must be whole numbers.'}, status=400)
            page = Paginator(qs, size).get_page(num)
            return Response({'count': page.paginator.count, 'page': page.number, 'page_size': size,
                             'total_pages': page.paginator.num_pages, 'results': rows(page.object_list)})
        data = rows(qs)
        return Response({'count': len(data), 'total_cost': round(sum(r['cost'] for r in data), 2), 'results': data})


class MovementSummaryView(APIView):
    """
    GET /api/inventory/movements/summary/?type=used&date_from=2026-11-01&date_to=2026-11-17
        (+ optional appointment_id, item_id, created_by_id — same filters and scoping as /movements/)
    Totals per item for the period. date_from and date_to are required.
    total_quantity is the amount moved (always positive); net_quantity keeps the sign
    (negative = stock went out).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count, Sum, Max, Min, F, ExpressionWrapper, DecimalField, Case, When, IntegerField
        qs, date_from, date_to, error = _filtered_movements(request, require_dates=True)
        if error:
            return error
        rows = (qs.values('item_id', 'item__name', 'item__unit', 'item__cost_per_unit')
                .annotate(use_count=Count('id'),
                          net_quantity=Sum('quantity'),
                          total_out=Sum(Case(When(quantity__lt=0, then=-F('quantity')), default=0, output_field=IntegerField())),
                          total_in=Sum(Case(When(quantity__gt=0, then=F('quantity')), default=0, output_field=IntegerField())),
                          last_used_at=Max('created_at'))
                .order_by('-use_count', 'item__name'))
        items = []
        for r in rows:
            total = (r['total_out'] or 0) + (r['total_in'] or 0)
            items.append({
                'item_id':        r['item_id'],
                'item_name':      r['item__name'],
                'unit':           r['item__unit'],
                'total_quantity': total,
                'net_quantity':   r['net_quantity'] or 0,
                'use_count':      r['use_count'],
                'total_cost':     round(total * float(r['item__cost_per_unit'] or 0), 2),
                'last_used_at':   timezone.localtime(r['last_used_at']) if r['last_used_at'] else None,
            })
        return Response({
            'date_from':      date_from,
            'date_to':        date_to,
            'item_count':     len(items),
            'total_uses':     sum(i['use_count'] for i in items),
            'total_cost':     round(sum(i['total_cost'] for i in items), 2),
            'items':          items,
        })


# ── Suppliers ─────────────────────────────────────────────────────────────────

SUPPLIER_FIELDS = ('name', 'phone', 'email', 'notes')


def _validate_supplier(data, partial=False):
    errors = {}
    if not partial or 'name' in data:
        if not str(data.get('name', '') or '').strip():
            errors['name'] = 'This field is required.'
    if data.get('email'):
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_email(data['email'])
        except DjangoValidationError:
            errors['email'] = 'Enter a valid email address.'
    return errors


class SupplierListView(APIView):
    """
    GET  /api/suppliers/?search=&include_inactive=true
    POST /api/suppliers/   {name, phone?, email?, notes?}
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Supplier.objects.all()
        if request.query_params.get('include_inactive', '').lower() not in ('1', 'true'):
            qs = qs.filter(is_active=True)
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        from django.db.models import Count
        qs = qs.annotate(item_count=Count('items'))
        return Response([{**serialize_supplier(s), 'item_count': s.item_count} for s in qs])

    def post(self, request):
        errors = _validate_supplier(request.data)
        if errors:
            return Response(errors, status=400)
        s = Supplier.objects.create(**{f: (request.data.get(f) or '') for f in SUPPLIER_FIELDS})
        return Response(serialize_supplier(s), status=201)


class SupplierDetailView(APIView):
    """
    GET    /api/suppliers/<id>/   — supplier + the items it supplies
    PATCH  /api/suppliers/<id>/   {name?, phone?, email?, notes?, is_active?}
    DELETE /api/suppliers/<id>/   — deactivates it (kept for stock history; linked items are unlinked)
    """
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        s = Supplier.objects.filter(pk=pk).first()
        if not s:
            return Response({'error': 'Supplier not found.'}, status=404)
        return Response({**serialize_supplier(s), 'items': [
            {'id': i.id, 'name': i.name, 'current_stock': i.current_stock, 'unit': i.unit,
             'cost_per_unit': float(i.cost_per_unit)} for i in s.items.all()
        ]})

    def patch(self, request, pk):
        s = Supplier.objects.filter(pk=pk).first()
        if not s:
            return Response({'error': 'Supplier not found.'}, status=404)
        errors = _validate_supplier(request.data, partial=True)
        if errors:
            return Response(errors, status=400)
        for f in SUPPLIER_FIELDS:
            if f in request.data:
                setattr(s, f, request.data[f] or '')
        if 'is_active' in request.data:
            s.is_active = bool(request.data['is_active'])
        s.save()
        # keep the legacy text on linked items in step
        s.items.update(supplier_name=s.name, supplier_phone=s.phone)
        return Response(serialize_supplier(s))

    def delete(self, request, pk):
        s = Supplier.objects.filter(pk=pk).first()
        if not s:
            return Response({'error': 'Supplier not found.'}, status=404)
        with transaction.atomic():
            unlinked = s.items.update(supplier=None)
            s.is_active = False
            s.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'Supplier deleted.', 'items_unlinked': unlinked})
