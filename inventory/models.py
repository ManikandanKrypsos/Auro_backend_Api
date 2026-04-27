from django.db import models


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('consumable',  'Consumable'),
        ('equipment',   'Equipment'),
        ('product',     'Product'),
        ('disposable',  'Disposable'),
    ]

    UNIT_CHOICES = [
        ('piece',       'Piece'),
        ('bottle',      'Bottle'),
        ('box',         'Box'),
        ('ml',          'ml'),
        ('g',           'g'),
        ('pair',        'Pair'),
        ('set',         'Set'),
        ('roll',        'Roll'),
    ]

    # Basic Info
    name                 = models.CharField(max_length=150)
    description          = models.TextField(blank=True)
    category             = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit                 = models.CharField(max_length=20, choices=UNIT_CHOICES)

    # Stock Control
    current_stock        = models.PositiveIntegerField(default=0)
    minimum_stock_alert  = models.PositiveIntegerField(default=0)
    last_restock_date    = models.DateField(null=True, blank=True)

    # Supplier Info (optional)
    supplier_name        = models.CharField(max_length=150, blank=True)
    supplier_phone       = models.CharField(max_length=30, blank=True)
    cost_per_unit        = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock_alert


class StockMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = [
        ('added',       'Added to Inventory'),
        ('used',        'Used in Treatment'),
        ('adjusted',    'Manual Adjustment'),
        ('ordered',     'Order More'),
    ]

    item       = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    type       = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity   = models.IntegerField()  # positive = added, negative = used
    note       = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item.name} {self.type} {self.quantity}"