from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0003_update_lead_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE leads_lead ALTER COLUMN score SET DEFAULT 0;",
            reverse_sql="SELECT 1;",
        ),
    ]