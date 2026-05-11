from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0007_patient_image_textfield'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE patients_sessionnote ALTER COLUMN advice_given TYPE jsonb USING advice_given::jsonb;",
            reverse_sql="ALTER TABLE patients_sessionnote ALTER COLUMN advice_given TYPE text USING advice_given::text;",
        ),
    ]