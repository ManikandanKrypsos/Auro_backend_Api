import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),
        ('rooms', '0001_initial'),
        ('treatments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='price_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='treatments.priceplan'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='duration',
            field=models.PositiveIntegerField(default=60, help_text='Duration in minutes'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='session_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='appointment',
            name='total_sessions',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient_arrived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='appointment',
            name='consent_status',
            field=models.CharField(choices=[('pending','Pending'),('signed','Signed')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='appointment',
            name='consent_form_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_status',
            field=models.CharField(choices=[('pending','Pending'),('paid','Paid'),('refunded','Refunded')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_type',
            field=models.CharField(choices=[('single','Single'),('package','Package')], default='single', max_length=20),
        ),
        migrations.AddField(
            model_name='appointment',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(choices=[('upcoming','Upcoming'),('completed','Completed'),('cancelled','Cancelled'),('no_show','No Show')], default='upcoming', max_length=20),
        ),
        migrations.AddField(
            model_name='appointment',
            name='room_fk',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='rooms.room'),
        ),
        migrations.RunSQL(
            sql="ALTER TABLE appointments_appointment ALTER COLUMN room DROP NOT NULL;",
            reverse_sql="SELECT 1;",
        ),
    ]