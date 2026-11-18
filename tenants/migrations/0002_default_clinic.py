import os

from django.db import migrations


def create_default_clinic(apps, schema_editor):
    """The clinic every existing record is moved into (the current single-clinic data)."""
    Clinic = apps.get_model('tenants', 'Clinic')
    if not Clinic.objects.exists():
        Clinic.objects.create(name=os.environ.get('DEFAULT_CLINIC_NAME', 'Aura Skin Care Clinic'))


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_clinic, migrations.RunPython.noop),
    ]
