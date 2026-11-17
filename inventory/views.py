import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin
from .models import InventoryItem, StockMovement, Supplier
from .serializers import (
    InventoryItemSerializer, InventoryItemListSerializer,
    InventoryItemWriteSerializer, StockMovementSerializer,
    StockMovementWriteSerializer, serialize_supplier,
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
            ],
            'adjust_reasons': [
                {'value': 'wastage',          'label': 'Wastage (lost / damaged / expired)'},
                {'value': 'count_correction', 'label': 'Count correction'},
            ],
        })


class InventoryListView(APIView):
    """
    GET  /api/inventory/           — list all items
         ?search=                  filter by name
         ?category=consumable      filter by category
         ?low_stock=true           show only low stock items

    POST /api/inventory/           — add new item (admin only)
    """
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        items     = InventoryItem.objects.all()
        search    = request.query_params.get('search', '').strip()
        category  = request.query_params.get('category', '').strip()
        low_stock = request.query_params.get('low_stock', '').strip()

        if search:
            items = items.filter(name__icontains=search)
        if category:
            items = items.filter(category=category)
        if low_stock == 'true':
            # Filter items where current_stock <= minimum_stock_alert
            from django.db.models import F
            items = items.filter(current_stock__lte=F('minimum_stock_alert'))

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
        movements = list(StockMovement.objects.filter(item=item).select_related('supplier', 'created_by'))
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

        # Prevent stock going negative
        new_stock = item.current_stock + quantity
        if new_stock < 0:
            return Response(
                {'error': f'Insufficient stock. Current stock is {item.current_stock}.'},
                status=400
            )

        # Save movement
        movement = StockMovement.objects.create(
            item=item, type=mtype, quantity=quantity, note=note, created_by=request.user
        )

        # Update item stock
        item.current_stock = new_stock
        if mtype in ['added', 'ordered']:
            item.last_restock_date = datetime.date.today()
        item.save()

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
    Body: {"quantity": 10, "unit_cost": 12.50, "supplier_id": 3, "note": "Invoice 4411"}
    quantity is required (whole number > 0); the rest is optional.
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
        unit_cost = request.data.get('unit_cost')
        if unit_cost not in (None, ''):
            try:
                unit_cost = Decimal(str(unit_cost)).quantize(Decimal('0.01'))
                if unit_cost < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                errors['unit_cost'] = 'Must be a number of 0 or more.'
        else:
            unit_cost = None
        supplier = None
        if request.data.get('supplier_id') not in (None, ''):
            supplier = Supplier.objects.filter(pk=request.data['supplier_id'], is_active=True).first()
            if not supplier:
                errors['supplier_id'] = 'Supplier not found.'
        if errors:
            return Response(errors, status=400)

        with transaction.atomic():
            item = _locked_item(pk)
            if not item:
                return Response({'error': 'Item not found.'}, status=404)
            item.current_stock += quantity
            item.last_restock_date = timezone.localdate()
            if unit_cost is not None:
                item.cost_per_unit = unit_cost
            item.save()
            movement = StockMovement.objects.create(
                item=item, type='received', quantity=quantity, unit_cost=unit_cost,
                supplier=supplier or item.supplier, note=str(request.data.get('note', ''))[:255],
                created_by=request.user,
            )
        return _movement_response(item, movement, f'Received {quantity} {item.unit}.')


class AdjustStockView(APIView):
    """
    POST /api/inventory/<id>/adjust/
    Body: {"quantity_delta": -2, "reason": "wastage" | "count_correction", "note": "Broken vial"}
    quantity_delta is a non-zero whole number (negative removes stock, positive adds).
    Wastage must be negative. Stock can't go below zero.
    """
    permission_classes = [IsAdmin]
    REASON_TO_TYPE = {'wastage': 'wastage', 'count_correction': 'correction'}

    def post(self, request, pk):
        errors = {}
        try:
            delta = int(request.data.get('quantity_delta'))
            if delta == 0:
                raise ValueError
        except (TypeError, ValueError):
            errors['quantity_delta'] = 'A non-zero whole number is required (negative removes stock).'
            delta = None
        reason = request.data.get('reason')
        if reason not in self.REASON_TO_TYPE:
            errors['reason'] = 'Use "wastage" or "count_correction".'
        elif reason == 'wastage' and delta is not None and delta > 0:
            errors['quantity_delta'] = 'Wastage removes stock, so quantity_delta must be negative.'
        if errors:
            return Response(errors, status=400)

        with transaction.atomic():
            item = _locked_item(pk)
            if not item:
                return Response({'error': 'Item not found.'}, status=404)
            if item.current_stock + delta < 0:
                return Response({'quantity_delta': f'Only {item.current_stock} {item.unit} in stock.'}, status=400)
            item.current_stock += delta
            item.save()
            movement = StockMovement.objects.create(
                item=item, type=self.REASON_TO_TYPE[reason], quantity=delta,
                note=str(request.data.get('note', ''))[:255], created_by=request.user,
            )
        return _movement_response(item, movement, 'Stock adjusted.')


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
