from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0005_appointment_package'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(
                choices=[
                    ('upcoming',   'Upcoming'),
                    ('in_session', 'In Session'),
                    ('completed',  'Completed'),
                    ('cancelled',  'Cancelled'),
                ],
                default='upcoming',
                max_length=20,
            ),
        ),
    ]