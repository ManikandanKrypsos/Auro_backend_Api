from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0002_update_treatment_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='treatment',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True),
        ),
    ]