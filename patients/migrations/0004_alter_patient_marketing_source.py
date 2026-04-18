from django.db import migrations, models


def fix_marketing_source_data(apps, schema_editor):
    """Fix all invalid marketing_source values before changing column type"""
    vendor = schema_editor.connection.vendor

    with schema_editor.connection.cursor() as cursor:
        if vendor == 'postgresql':
            # PostgreSQL — need to handle text column differently
            # First set all non-numeric values to NULL
            cursor.execute("""
                UPDATE patients_patient
                SET marketing_source = NULL
                WHERE marketing_source IS NULL
                OR marketing_source = ''
                OR marketing_source ~ '[^0-9]'
                OR marketing_source NOT IN ('1','2','3','4','5','6')
            """)
        elif vendor == 'mysql':
            cursor.execute("""
                UPDATE patients_patient
                SET marketing_source = NULL
                WHERE marketing_source = ''
                OR marketing_source IS NULL
                OR marketing_source NOT REGEXP '^[1-6]$'
            """)


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_alter_patient_blood_type_alter_patient_gender_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_marketing_source_data,
            reverse_fix,
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