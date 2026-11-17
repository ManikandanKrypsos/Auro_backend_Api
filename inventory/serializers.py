from rest_framework import serializers
from django.utils import timezone

from .models import InventoryItem, StockMovement, Supplier, Lot

CATEGORY_MAP = {
    1: 'consumable',
    2: 'equipment',
    3: 'product',
    4: 'disposable',
}
CATEGORY_ID_MAP = {v: k for k, v in CATEGORY_MAP.items()}

UNIT_MAP = {
    1: 'ml',
    2: 'pcs',
    3: 'units',
    4: 'kg',
    5: 'g',
    6: 'l',
}
UNIT_ID_MAP = {v: k for k, v in UNIT_MAP.items()}


def serialize_supplier(s):
    return {
        'id': s.id, 'name': s.name, 'phone': s.phone, 'email': s.email, 'notes': s.notes,
        'is_active': s.is_active, 'created_at': s.created_at, 'updated_at': s.updated_at,
    }


def serialize_lot(lot, today=None):
    today = today or timezone.localdate()
    return {
        'id':                 lot.id,
        'inventory_item_id':  lot.item_id,
        'item_name':          lot.item.name,
        'lot_number':         lot.lot_number,
        'expiry_date':        lot.expiry_date,
        'days_to_expiry':     (lot.expiry_date - today).days if lot.expiry_date else None,
        'is_expired':         bool(lot.expiry_date and lot.expiry_date < today),
        'quantity_received':  lot.quantity_received,
        'quantity_remaining': lot.quantity_remaining,
        'unit_cost':          float(lot.unit_cost) if lot.unit_cost is not None else None,
        'supplier_id':        lot.supplier_id,
        'supplier_name':      lot.supplier.name if lot.supplier_id else None,
        'received_at':        lot.received_at,
    }


class StockMovementSerializer(serializers.ModelSerializer):
    type_label      = serializers.CharField(source='get_type_display', read_only=True)
    unit_cost       = serializers.FloatField(read_only=True, allow_null=True)
    supplier_name   = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = StockMovement
        fields = ['id', 'type', 'type_label', 'quantity', 'unit_cost', 'supplier_id', 'supplier_name',
                  'lot_id', 'lot_number', 'purchase_order_id', 'purchase_order_number',
                  'note', 'created_by_id', 'created_by_name', 'created_at']
        read_only_fields = ['created_at']

    lot_number            = serializers.SerializerMethodField()
    purchase_order_number = serializers.SerializerMethodField()

    def get_supplier_name(self, obj):
        return obj.supplier.name if obj.supplier_id else None

    def get_lot_number(self, obj):
        return obj.lot.lot_number if obj.lot_id else None

    def get_purchase_order_number(self, obj):
        return obj.purchase_order.number if obj.purchase_order_id else None

    def get_created_by_name(self, obj):
        u = obj.created_by
        return (u.username or u.email.split('@')[0]) if u else None


class SupplierFieldsMixin:
    """cost_per_unit as a number + the linked supplier."""

    def get_stock_value(self, obj):
        return round(obj.current_stock * float(obj.cost_per_unit or 0), 2)

    def get_stock_status(self, obj):
        if obj.current_stock <= 0:
            return 'out_of_stock'
        return 'low_stock' if obj.current_stock <= obj.minimum_stock_alert else 'in_stock'

    def get_next_expiry_date(self, obj):
        if not obj.track_lots:
            return None
        if hasattr(obj, 'next_expiry'):          # annotated by the list view
            return obj.next_expiry
        lot = obj.lots.filter(quantity_remaining__gt=0, expiry_date__isnull=False).order_by('expiry_date').first()
        return lot.expiry_date if lot else None

    def get_supplier(self, obj):
        s = obj.supplier
        return {'id': s.id, 'name': s.name, 'phone': s.phone, 'email': s.email, 'is_active': s.is_active} if s else None


class InventoryItemSerializer(SupplierFieldsMixin, serializers.ModelSerializer):
    """Read serializer — full detail with IDs and computed fields."""
    category_id  = serializers.SerializerMethodField()
    unit_id      = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    cost_per_unit = serializers.FloatField(read_only=True)
    supplier     = serializers.SerializerMethodField()
    stock_value  = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    next_expiry_date = serializers.SerializerMethodField()
    movements    = StockMovementSerializer(many=True, read_only=True)

    class Meta:
        model  = InventoryItem
        fields = [
            'id', 'name', 'description', 'sku', 'brand',
            'category', 'category_id',
            'unit', 'unit_id',
            'current_stock', 'minimum_stock_alert', 'is_low_stock', 'stock_status', 'stock_value',
            'track_lots', 'next_expiry_date',
            'last_restock_date',
            'supplier_id', 'supplier', 'supplier_name', 'supplier_phone', 'cost_per_unit',
            'created_at', 'updated_at',
            'movements',
        ]

    def get_category_id(self, obj):
        return CATEGORY_ID_MAP.get(obj.category)

    def get_unit_id(self, obj):
        return UNIT_ID_MAP.get(obj.unit)

    def get_is_low_stock(self, obj):
        return obj.is_low_stock


class InventoryItemListSerializer(SupplierFieldsMixin, serializers.ModelSerializer):
    """Light serializer for list view — no movements."""
    category_id  = serializers.SerializerMethodField()
    unit_id      = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    cost_per_unit = serializers.FloatField(read_only=True)
    supplier     = serializers.SerializerMethodField()
    stock_value  = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    next_expiry_date = serializers.SerializerMethodField()

    class Meta:
        model  = InventoryItem
        fields = [
            'id', 'name', 'description', 'sku', 'brand',
            'category', 'category_id',
            'unit', 'unit_id',
            'current_stock', 'minimum_stock_alert', 'is_low_stock', 'stock_status', 'stock_value',
            'track_lots', 'next_expiry_date',
            'last_restock_date',
            'supplier_id', 'supplier', 'supplier_name', 'supplier_phone', 'cost_per_unit',
            'created_at', 'updated_at',
        ]

    def get_category_id(self, obj):
        return CATEGORY_ID_MAP.get(obj.category)

    def get_unit_id(self, obj):
        return UNIT_ID_MAP.get(obj.unit)

    def get_is_low_stock(self, obj):
        return obj.is_low_stock


class InventoryItemWriteSerializer(serializers.Serializer):
    """
    Write serializer for POST and PATCH.

    Body:
    {
        "name":                 "Juvederm Voluma",
        "description":          "Premium Post-Treatment Glow",
        "category_id":          1,
        "unit_id":              2,
        "initial_stock":        20,
        "minimum_stock_alert":  10,
        "supplier_id":          3,        // linked supplier (null to unlink)
        "supplier_name":        "AURA Luxe Lab",       // legacy free text, still accepted
        "supplier_phone":       "+1 (800) 555-0192",
        "cost_per_unit":        25.00,
        "sku":                  "RST-30G-001",   // optional
        "brand":                "Restylane",     // optional
        "track_lots":           true             // stock split into lots with expiry dates
    }
    category can be sent as category_id (1-4) or category ("consumable"…).
    """
    name                 = serializers.CharField(max_length=150, required=False)
    description          = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    sku                  = serializers.CharField(max_length=60, required=False, allow_blank=True, allow_null=True)
    brand                = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    track_lots           = serializers.BooleanField(required=False)
    category_id          = serializers.IntegerField(required=False)
    category             = serializers.ChoiceField(choices=list(CATEGORY_ID_MAP.keys()), required=False)
    supplier_id          = serializers.IntegerField(required=False, allow_null=True)
    unit_id              = serializers.IntegerField(required=False)
    initial_stock        = serializers.IntegerField(min_value=0, required=False)
    minimum_stock_alert  = serializers.IntegerField(min_value=0, required=False)
    supplier_name        = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True, default='')
    supplier_phone       = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True, default='')
    cost_per_unit        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_category_id(self, value):
        if value not in CATEGORY_MAP:
            raise serializers.ValidationError(
                "Invalid category_id. Use 1=Consumable, 2=Equipment, 3=Product, 4=Disposable"
            )
        return value

    def validate_supplier_id(self, value):
        if value is not None and not Supplier.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError(f"Supplier {value} not found.")
        return value

    def _apply_category_and_supplier(self, target, validated_data):
        """category_id / category / supplier_id → model fields. target is a dict (create) or an item (update)."""
        def put(field, value):
            if isinstance(target, dict):
                target[field] = value
            else:
                setattr(target, field, value)
        category_id = validated_data.pop('category_id', None)
        category    = validated_data.pop('category', None)
        if category_id:
            put('category', CATEGORY_MAP[category_id])
        elif category:
            put('category', category)
        if 'supplier_id' in validated_data:
            supplier_id = validated_data.pop('supplier_id')
            supplier = Supplier.objects.get(pk=supplier_id) if supplier_id else None
            put('supplier', supplier)
            if supplier:   # keep the legacy text fields in step for older screens
                validated_data.pop('supplier_name', None)
                validated_data.pop('supplier_phone', None)
                put('supplier_name', supplier.name)
                put('supplier_phone', supplier.phone)
            else:          # unlinked: clear the legacy text too, unless new text was sent
                if 'supplier_name' not in validated_data:
                    put('supplier_name', '')
                if 'supplier_phone' not in validated_data:
                    put('supplier_phone', '')

    def validate_unit_id(self, value):
        if value not in UNIT_MAP:
            raise serializers.ValidationError(
                "Invalid unit_id. Use 1=ml, 2=pcs, 3=units, 4=kg, 5=g, 6=l"
            )
        return value

    def create(self, validated_data):
        initial_stock = validated_data.pop('initial_stock', 0)
        unit_id       = validated_data.pop('unit_id', None)

        self._apply_category_and_supplier(validated_data, validated_data)
        if unit_id:
            validated_data['unit'] = UNIT_MAP[unit_id]

        # Set defaults for optional fields to avoid NOT NULL DB constraint
        validated_data.setdefault('description',    '')
        validated_data.setdefault('supplier_name',  '')
        validated_data.setdefault('supplier_phone', '')

        # Replace None with empty string for these fields
        for field in ['description', 'supplier_name', 'supplier_phone', 'sku', 'brand']:
            if validated_data.get(field) is None:
                validated_data[field] = ''

        validated_data['current_stock'] = initial_stock
        item = InventoryItem.objects.create(**validated_data)

        # Record initial stock movement
        if initial_stock > 0:
            import datetime
            StockMovement.objects.create(
                item=item, type='added',
                quantity=initial_stock,
                note='Initial stock',
                unit_cost=item.cost_per_unit,
                supplier=item.supplier,
                created_by=self.context.get('user'),
            )
            item.last_restock_date = datetime.date.today()
            item.save()

        return item

    def update(self, instance, validated_data):
        initial_stock = validated_data.pop('initial_stock', None)
        unit_id       = validated_data.pop('unit_id', None)

        self._apply_category_and_supplier(instance, validated_data)
        if unit_id:
            instance.unit = UNIT_MAP[unit_id]

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Fix null values for NOT NULL fields
        for field in ['description', 'supplier_name', 'supplier_phone', 'sku', 'brand']:
            if getattr(instance, field, None) is None:
                setattr(instance, field, '')

        # If initial_stock is sent during update treat as stock adjustment
        if initial_stock is not None:
            diff = initial_stock - instance.current_stock
            if diff != 0:
                import datetime
                StockMovement.objects.create(
                    item=instance, type='adjusted',
                    quantity=diff,
                    note='Manual stock adjustment',
                    created_by=self.context.get('user'),
                )
                instance.current_stock     = initial_stock
                instance.last_restock_date = datetime.date.today()

        instance.save()
        return instance


class StockMovementWriteSerializer(serializers.Serializer):
    """
    Used by POST /api/inventory/<id>/movements/

    Body:
    {
        "type":     "added",      // added | used | adjusted | ordered
        "quantity": 20,           // positive for add, negative for used
        "note":     "Restocked"
    }
    """
    type     = serializers.ChoiceField(choices=['added', 'used', 'adjusted', 'ordered'])
    quantity = serializers.IntegerField()
    note     = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, data):
        if data['type'] in ['used'] and data['quantity'] > 0:
            data['quantity'] = -abs(data['quantity'])
        if data['type'] in ['added', 'ordered'] and data['quantity'] < 0:
            data['quantity'] = abs(data['quantity'])
        return data