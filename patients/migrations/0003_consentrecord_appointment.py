import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('patients', '0002_sessionnote'),
        ('appointments', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='consentrecord',
            name='appointment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='consent_records',
                to='appointments.appointment',
            ),
        ),
    ]