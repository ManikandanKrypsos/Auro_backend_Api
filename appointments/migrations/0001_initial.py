from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('patients', '0001_initial'),
        ('rooms', '0001_initial'),
        ('treatments', '0001_initial'),
        ('packages', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField()),
                ('duration', models.PositiveIntegerField(default=60, help_text='Duration in minutes')),
                ('session_number', models.PositiveIntegerField(default=1)),
                ('total_sessions', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('upcoming','Upcoming'),('in_session','In Session'),('completed','Completed'),('cancelled','Cancelled')], default='upcoming', max_length=20)),
                ('patient_arrived', models.BooleanField(default=False)),
                ('consent_status', models.CharField(choices=[('pending','Pending'),('signed','Signed')], default='pending', max_length=20)),
                ('consent_form_url', models.URLField(blank=True)),
                ('payment_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('payment_status', models.CharField(choices=[('pending','Pending'),('paid','Paid'),('refunded','Refunded')], default='pending', max_length=20)),
                ('payment_type', models.CharField(choices=[('online','Online Payment'),('cash','Cash')], default='cash', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='patients.patient')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to=settings.AUTH_USER_MODEL)),
                ('treatment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='treatments.treatment')),
                ('room_fk', models.ForeignKey(blank=True, db_column='room_fk_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='rooms.room')),
                ('price_plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='treatments.priceplan')),
                ('package', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='packages.patientpackage')),
            ],
            options={'ordering': ['date_time']},
        ),
    ]