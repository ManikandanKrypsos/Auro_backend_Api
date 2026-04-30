from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0002_update_appointment'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE appointments_appointment 
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
            """,
            reverse_sql="SELECT 1;",
        ),
    ]