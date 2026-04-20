from django.db import migrations, models


def generate_patient_ids(apps, schema_editor):
    """Generate patient_id for all existing patients"""
    Patient = apps.get_model('patients', 'Patient')
    for patient in Patient.objects.all():
        patient.patient_id = f'Aura{patient.id}'
        patient.save()


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0004_alter_patient_marketing_source'),
    ]

    operations = [
        # Step 1 — Add field without unique constraint first
        migrations.AddField(
            model_name='patient',
            name='patient_id',
            field=models.CharField(max_length=20, blank=True, default=''),
        ),
        # Step 2 — Fill in the data
        migrations.RunPython(
            generate_patient_ids,
            migrations.RunPython.noop
        ),
        # Step 3 — Now add unique constraint
        migrations.AlterField(
            model_name='patient',
            name='patient_id',
            field=models.CharField(max_length=20, unique=True, blank=True),
        ),
    ]