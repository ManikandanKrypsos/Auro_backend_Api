from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0005_fix_all_old_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='room_types',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunSQL(
            sql="ALTER TABLE treatments_treatment ALTER COLUMN pre_care_old DROP NOT NULL;",
            reverse_sql="SELECT 1;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE treatments_treatment ALTER COLUMN post_care_old DROP NOT NULL;",
            reverse_sql="SELECT 1;",
        ),
    ]