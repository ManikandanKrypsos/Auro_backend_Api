from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0006_treatment_room_types'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE treatments_treatment ALTER COLUMN room_type DROP NOT NULL;",
            reverse_sql="SELECT 1;",
        ),
    ]