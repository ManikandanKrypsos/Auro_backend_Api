from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_fix_missing_columns'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='payment_type',
            field=models.CharField(
                choices=[('online', 'Online Payment'), ('cash', 'Cash')],
                default='cash',
                max_length=20,
            ),
        ),
    ]