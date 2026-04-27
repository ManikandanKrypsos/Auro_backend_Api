from rest_framework import serializers
from .models import InventoryItem, StockMovement

CATEGORY_MAP = {
    1: 'consumable',
    2: 'equipment',
    3: 'product',
    4: 'disposable',
}
CATEGORY_ID_MAP = {v: k for k, v in CATEGORY_MAP.items()}

UNIT_MAP = {
    1: 'piece',
    2: 'bottle',
    3: 'box',
    4: 'ml',
    5: 'g',
    6: 'pair',
    7: 'set',
    8: 'roll',
}
UNIT_ID_MAP = {v: k for k, v in UNIT_MAP.items()}


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StockMovement
        fields = ['id', 'type', 'quantity', 'note', 'created_at']
        read_only_fields = ['created_at']


class InventoryItemSerializer(serializers.ModelSerializer):
    """Read serializer — full detail with IDs and computed fields."""
    category_id  = serializers.SerializerMethodField()
    unit_id      = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    movements    = StockMovementSerializer(many=True, read_only=True)

    class Meta:
        model  = InventoryItem
        fields = [
            'id', 'name', 'description',
            'category', 'category_id',
            'unit', 'unit_id',
            'current_stock', 'minimum_stock_alert', 'is_low_stock',
            'last_restock_date',
            'supplier_name', 'supplier_phone', 'cost_per_unit',
            'created_at', 'updated_at',
            'movements',
        ]

    def get_category_id(self, obj):
        return CATEGORY_ID_MAP.get(obj.category)

    def get_unit_id(self, obj):
        return UNIT_ID_MAP.get(obj.unit)

    def get_is_low_stock(self, obj):
        return obj.is_low_stock


class InventoryItemListSerializer(serializers.ModelSerializer):
    """Light serializer for list view — no movements."""
    category_id  = serializers.SerializerMethodField()
    unit_id      = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model  = InventoryItem
        fields = [
            'id', 'name', 'description',
            'category', 'category_id',
            'unit', 'unit_id',
            'current_stock', 'minimum_stock_alert', 'is_low_stock',
            'last_restock_date',
            'supplier_name', 'supplier_phone', 'cost_per_unit',
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
        "supplier_name":        "AURA Luxe Lab",
        "supplier_phone":       "+1 (800) 555-0192",
        "cost_per_unit":        25.00
    }
    """
    name                 = serializers.CharField(max_length=150, required=False)
    description          = serializers.CharField(required=False, allow_blank=True)
    category_id          = serializers.IntegerField(required=False)
    unit_id              = serializers.IntegerField(required=False)
    initial_stock        = serializers.IntegerField(min_value=0, required=False)
    minimum_stock_alert  = serializers.IntegerField(min_value=0, required=False)
    supplier_name        = serializers.CharField(max_length=150, required=False, allow_blank=True)
    supplier_phone       = serializers.CharField(max_length=30, required=False, allow_blank=True)
    cost_per_unit        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_category_id(self, value):
        if value not in CATEGORY_MAP:
            raise serializers.ValidationError(
                "Invalid category_id. Use 1=Consumable, 2=Equipment, 3=Product, 4=Disposable"
            )
        return value

    def validate_unit_id(self, value):
        if value not in UNIT_MAP:
            raise serializers.ValidationError(
                "Invalid unit_id. Use 1=Piece, 2=Bottle, 3=Box, 4=ml, 5=g, 6=Pair, 7=Set, 8=Roll"
            )
        return value

    def create(self, validated_data):
        initial_stock = validated_data.pop('initial_stock', 0)
        category_id   = validated_data.pop('category_id', None)
        unit_id       = validated_data.pop('unit_id', None)

        if category_id:
            validated_data['category'] = CATEGORY_MAP[category_id]
        if unit_id:
            validated_data['unit'] = UNIT_MAP[unit_id]

        validated_data['current_stock'] = initial_stock
        item = InventoryItem.objects.create(**validated_data)

        # Record initial stock movement
        if initial_stock > 0:
            import datetime
            StockMovement.objects.create(
                item=item, type='added',
                quantity=initial_stock,
                note='Initial stock'
            )
            item.last_restock_date = datetime.date.today()
            item.save()

        return item

    def update(self, instance, validated_data):
        initial_stock = validated_data.pop('initial_stock', None)
        category_id   = validated_data.pop('category_id', None)
        unit_id       = validated_data.pop('unit_id', None)

        if category_id:
            instance.category = CATEGORY_MAP[category_id]
        if unit_id:
            instance.unit = UNIT_MAP[unit_id]

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # If initial_stock is sent during update treat as stock adjustment
        if initial_stock is not None:
            diff = initial_stock - instance.current_stock
            if diff != 0:
                import datetime
                StockMovement.objects.create(
                    item=instance, type='adjusted',
                    quantity=diff,
                    note='Manual stock adjustment'
                )
                instance.current_stock  = initial_stock
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