import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin
from .models import InventoryItem, StockMovement
from .serializers import (
    InventoryItemSerializer, InventoryItemListSerializer,
    InventoryItemWriteSerializer, StockMovementSerializer,
    StockMovementWriteSerializer,
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
            ],
        })


class InventoryListView(APIView):
    """
    GET  /api/inventory/           — list all items
         ?search=                  filter by name
         ?category=consumable      filter by category
         ?low_stock=true           show only low stock items

    POST /api/inventory/           — add new item
    """
    permission_classes = [IsAdmin]

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
        serializer = InventoryItemWriteSerializer(data=request.data)
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
        serializer = InventoryItemWriteSerializer(item, data=request.data, partial=True)
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

        data = InventoryItemListSerializer(items, many=True).data
        return Response({
            'count':  len(data),
            'items':  data,
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
        movements = StockMovement.objects.filter(item=item)
        return Response(StockMovementSerializer(movements, many=True).data)

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
            item=item, type=mtype, quantity=quantity, note=note
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