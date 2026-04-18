from django.db import migrations, models


def fix_marketing_source_data(apps, schema_editor):
    """Fix all invalid marketing_source values before changing column type"""
    with schema_editor.connection.cursor() as cursor:
        vendor = schema_editor.connection.vendor
        if vendor == 'postgresql':
            cursor.execute("""
                UPDATE patients_patient
                SET marketing_source = NULL
                WHERE marketing_source::text = ''
                OR marketing_source::text NOT IN ('1','2','3','4','5','6')
            """)
        else:
            cursor.execute("""
                UPDATE patients_patient
                SET marketing_source = NULL
                WHERE marketing_source = ''
                OR marketing_source NOT IN ('1','2','3','4','5','6')
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_alter_patient_blood_type_alter_patient_gender_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_marketing_source_data,
            migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name='patient',
            name='marketing_source',
            field=models.IntegerField(
                blank=True,
                null=True,
                default=None,
                choices=[
                    (1, 'Instagram'),
                    (2, 'Website'),
                    (3, 'Walk-in'),
                    (4, 'Referral'),
                    (5, 'WhatsApp'),
                    (6, 'Other'),
                ]
            ),
        ),
    ]