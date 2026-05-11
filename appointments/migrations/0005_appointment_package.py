import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0004_update_payment_type'),
        ('packages',     '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='package',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='appointments',
                to='packages.patientpackage'
            ),
        ),
    ]