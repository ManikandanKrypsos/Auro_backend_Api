from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0007_patient_image_textfield'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Convert existing text to JSON array, wrapping plain text in array
                ALTER TABLE patients_sessionnote
                ADD COLUMN advice_given_new jsonb DEFAULT '[]'::jsonb;

                UPDATE patients_sessionnote
                SET advice_given_new = CASE
                    WHEN advice_given IS NULL OR advice_given = '' THEN '[]'::jsonb
                    WHEN advice_given::text LIKE '[%' THEN advice_given::jsonb
                    ELSE jsonb_build_array(advice_given)
                END;

                ALTER TABLE patients_sessionnote DROP COLUMN advice_given;
                ALTER TABLE patients_sessionnote RENAME COLUMN advice_given_new TO advice_given;
            """,
            reverse_sql="""
                ALTER TABLE patients_sessionnote
                ADD COLUMN advice_given_old text DEFAULT '';

                UPDATE patients_sessionnote
                SET advice_given_old = advice_given::text;

                ALTER TABLE patients_sessionnote DROP COLUMN advice_given;
                ALTER TABLE patients_sessionnote RENAME COLUMN advice_given_old TO advice_given;
            """,
        ),
    ]