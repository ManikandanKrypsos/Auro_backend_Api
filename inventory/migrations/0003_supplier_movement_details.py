from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def suppliers_from_free_text(apps, schema_editor):
    """Turn each distinct supplier_name on items into a Supplier and link the items to it."""
    Item = apps.get_model('inventory', 'InventoryItem')
    Supplier = apps.get_model('inventory', 'Supplier')
    by_name = {}
    for item in Item.objects.exclude(supplier_name=''):
        key = item.supplier_name.strip().lower()
        if not key:
            continue
        if key not in by_name:
            by_name[key] = Supplier.objects.create(name=item.supplier_name.strip(), phone=item.supplier_phone or '')
        item.supplier = by_name[key]
        item.save(update_fields=['supplier'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_category_default'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='items', to='inventory.supplier'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='unit_cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='movements', to='inventory.supplier'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='stock_movements', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='stockmovement',
            name='type',
            field=models.CharField(choices=[
                ('added', 'Added to Inventory'), ('used', 'Used in Treatment'), ('adjusted', 'Manual Adjustment'),
                ('ordered', 'Order More'), ('received', 'Received'), ('wastage', 'Wastage'),
                ('correction', 'Count Correction'),
            ], max_length=20),
        ),
        migrations.RunPython(suppliers_from_free_text, migrations.RunPython.noop),
    ]
