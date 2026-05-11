import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients',   '0006_sessionnote_consentrecord'),
        ('treatments', '0010_treatment_image_url_textfield'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientPackage',
            fields=[
                ('id',                  models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('total_sessions',      models.PositiveIntegerField()),
                ('sessions_completed',  models.PositiveIntegerField(default=0)),
                ('status',              models.CharField(choices=[('active','Active'),('completed','Completed'),('cancelled','Cancelled')], default='active', max_length=20)),
                ('payment_amount',      models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_type',        models.CharField(choices=[('online','Online Payment'),('cash','Cash')], default='cash', max_length=20)),
                ('payment_status',      models.CharField(choices=[('pending','Pending'),('paid','Paid'),('refunded','Refunded')], default='pending', max_length=20)),
                ('notes',               models.TextField(blank=True)),
                ('created_at',          models.DateTimeField(auto_now_add=True)),
                ('updated_at',          models.DateTimeField(auto_now=True)),
                ('patient',    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packages', to='patients.patient')),
                ('treatment',  models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packages', to='treatments.treatment')),
                ('price_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packages', to='treatments.priceplan')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]