from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0004_fix_price_column_sql'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE treatments_treatment ALTER COLUMN price DROP NOT NULL;
                ALTER TABLE treatments_treatment ALTER COLUMN pre_care_old DROP NOT NULL;
                ALTER TABLE treatments_treatment ALTER COLUMN post_care_old DROP NOT NULL;
                ALTER TABLE treatments_treatment ALTER COLUMN frequency DROP NOT NULL;
            """,
            reverse_sql="SELECT 1;",
        ),
    ]