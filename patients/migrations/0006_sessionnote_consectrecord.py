import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0005_auto_previous'),  # replace with your actual 0005 filename
        ('appointments', '0004_update_payment_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SessionNote',
            fields=[
                ('id',                     models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('treatment_name',         models.CharField(blank=True, max_length=150)),
                ('skin_observation',       models.TextField(blank=True)),
                ('advice_given',           models.TextField(blank=True)),
                ('products_used',          models.JSONField(blank=True, default=list)),
                ('recommended_to_patient', models.JSONField(blank=True, default=list)),
                ('next_treatment',         models.CharField(blank=True, max_length=255)),
                ('before_photo',           models.TextField(blank=True)),
                ('after_photo',            models.TextField(blank=True)),
                ('created_at',             models.DateTimeField(auto_now_add=True)),
                ('updated_at',             models.DateTimeField(auto_now=True)),
                ('patient',     models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_notes', to='patients.patient')),
                ('therapist',   models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='session_notes', to=settings.AUTH_USER_MODEL)),
                ('appointment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='session_note', to='appointments.appointment')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ConsentRecord',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('title',            models.CharField(max_length=150)),
                ('file_name',        models.CharField(blank=True, max_length=255)),
                ('file_url',         models.TextField(blank=True)),
                ('status',           models.CharField(choices=[('signed', 'Signed'), ('pending', 'Pending')], default='pending', max_length=10)),
                ('patient_signed',   models.BooleanField(default=False)),
                ('therapist_signed', models.BooleanField(default=False)),
                ('signed_date',      models.DateField(blank=True, null=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consent_records', to='patients.patient')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]