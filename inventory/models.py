from django.conf import settings
from django.db import models


class Supplier(models.Model):
    name       = models.CharField(max_length=150)
    phone      = models.CharField(max_length=30, blank=True)
    email      = models.EmailField(blank=True)
    notes      = models.TextField(blank=True)
    is_active  = models.BooleanField(default=True)   # DELETE deactivates, so history keeps the name
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('consumable',  'Consumable'),
        ('equipment',   'Equipment'),
        ('product',     'Product'),
        ('disposable',  'Disposable'),
    ]

    UNIT_CHOICES = [
        ('ml',    'ml'),
        ('pcs',   'pcs'),
        ('units', 'units'),
        ('kg',    'kg'),
        ('g',     'g'),
        ('l',     'l'),
    ]

    # Basic Info
    name                 = models.CharField(max_length=150)
    description          = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='product', blank=True)
    unit                 = models.CharField(max_length=20, choices=UNIT_CHOICES)

    # Stock Control
    current_stock        = models.PositiveIntegerField(default=0)
    minimum_stock_alert  = models.PositiveIntegerField(default=0)
    last_restock_date    = models.DateField(null=True, blank=True)

    # Supplier Info (optional)
    supplier_name        = models.CharField(max_length=150, blank=True)
    supplier_phone       = models.CharField(max_length=30, blank=True)
    supplier             = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
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
        ('received',    'Received'),
        ('wastage',     'Wastage'),
        ('correction',  'Count Correction'),
    ]

    item       = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    type       = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity   = models.IntegerField()  # positive = added, negative = used
    note       = models.CharField(max_length=255, blank=True)
    unit_cost  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier   = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item.name} {self.type} {self.quantity}"