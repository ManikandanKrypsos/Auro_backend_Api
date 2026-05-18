from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
    ]
    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='category',
            field=models.CharField(
                choices=[('consumable','Consumable'),('equipment','Equipment'),('product','Product'),('disposable','Disposable')],
                default='product',
                blank=True,
                max_length=20,
            ),
        ),
    ]