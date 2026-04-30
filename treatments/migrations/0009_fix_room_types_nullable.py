from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0008_treatment_rooms_m2m'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE treatments_treatment ALTER COLUMN room_types DROP NOT NULL;",
            reverse_sql="SELECT 1;",
        ),
    ]