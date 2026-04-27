import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id',                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name',                  models.CharField(max_length=150)),
                ('description',           models.TextField(blank=True)),
                ('category',              models.CharField(choices=[('consumable','Consumable'),('equipment','Equipment'),('product','Product'),('disposable','Disposable')], max_length=20)),
                ('unit',                  models.CharField(choices=[('piece','Piece'),('bottle','Bottle'),('box','Box'),('ml','ml'),('g','g'),('pair','Pair'),('set','Set'),('roll','Roll')], max_length=20)),
                ('current_stock',         models.PositiveIntegerField(default=0)),
                ('minimum_stock_alert',   models.PositiveIntegerField(default=0)),
                ('last_restock_date',     models.DateField(blank=True, null=True)),
                ('supplier_name',         models.CharField(blank=True, max_length=150)),
                ('supplier_phone',        models.CharField(blank=True, max_length=30)),
                ('cost_per_unit',         models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at',            models.DateTimeField(auto_now_add=True)),
                ('updated_at',            models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('type',       models.CharField(choices=[('added','Added to Inventory'),('used','Used in Treatment'),('adjusted','Manual Adjustment'),('ordered','Order More')], max_length=20)),
                ('quantity',   models.IntegerField()),
                ('note',       models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item',       models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movements', to='inventory.inventoryitem')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]