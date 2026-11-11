from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0002_fix_leadactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='next_action_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
