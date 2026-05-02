from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0002_auto_20240101_0000'),  # replace with your actual 0002 migration name
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='lead',
            name='stage',
            field=models.CharField(
                choices=[
                    ('new_inquiries', 'New Inquiries'),
                    ('engaged',       'Engaged'),
                    ('consultation',  'Consultation'),
                    ('winning',       'Winning'),
                    ('converted',     'Converted'),
                    ('lost',          'Lost'),
                ],
                default='new_inquiries', max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='lead',
            name='source',
            field=models.CharField(
                choices=[
                    ('instagram', 'Instagram'),
                    ('web',       'Web'),
                    ('walk_in',   'Walk-In'),
                    ('referral',  'Referral'),
                    ('whatsapp',  'WhatsApp'),
                    ('other',     'Other'),
                ],
                default='web', max_length=20
            ),
        ),
    ]