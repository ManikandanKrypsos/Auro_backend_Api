from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_alter_patient_blood_type_alter_patient_gender_and_more'),
    ]

    operations = [
        # Step 1 — First make the column nullable so bad data doesn't block us
        migrations.RunSQL(
            sql="ALTER TABLE patients_patient ALTER COLUMN marketing_source DROP NOT NULL",
            reverse_sql="ALTER TABLE patients_patient ALTER COLUMN marketing_source SET NOT NULL",
        ),
        # Step 2 — Set all invalid text values to NULL
        migrations.RunSQL(
            sql="""
                UPDATE patients_patient
                SET marketing_source = NULL
                WHERE marketing_source::text = ''
                OR marketing_source::text ~ '[^0-9]'
                OR marketing_source::text NOT IN ('1','2','3','4','5','6')
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Step 3 — Now safely change the field type
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