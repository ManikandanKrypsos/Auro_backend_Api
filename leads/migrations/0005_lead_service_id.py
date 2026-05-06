from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0004_fix_score_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='service_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]