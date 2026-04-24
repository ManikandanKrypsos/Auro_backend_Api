from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0003_fix_price_nullable'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE treatments_treatment ALTER COLUMN price DROP NOT NULL;",
            reverse_sql="ALTER TABLE treatments_treatment ALTER COLUMN price SET NOT NULL;",
        ),
    ]