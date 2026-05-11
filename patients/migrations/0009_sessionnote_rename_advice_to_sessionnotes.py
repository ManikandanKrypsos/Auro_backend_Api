from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0008_sessionnote_advice_jsonfield'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE patients_sessionnote
                ADD COLUMN IF NOT EXISTS session_notes jsonb DEFAULT '[]'::jsonb;

                UPDATE patients_sessionnote
                SET session_notes = advice_given
                WHERE advice_given IS NOT NULL;

                ALTER TABLE patients_sessionnote DROP COLUMN IF EXISTS advice_given;
            """,
            reverse_sql="""
                ALTER TABLE patients_sessionnote
                ADD COLUMN IF NOT EXISTS advice_given jsonb DEFAULT '[]'::jsonb;

                UPDATE patients_sessionnote
                SET advice_given = session_notes
                WHERE session_notes IS NOT NULL;

                ALTER TABLE patients_sessionnote DROP COLUMN IF EXISTS session_notes;
            """,
        ),
    ]