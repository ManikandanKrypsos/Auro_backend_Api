from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('patients', '0001_initial'),
        ('appointments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='SessionNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('treatment_name', models.CharField(blank=True, max_length=150)),
                ('skin_observation', models.TextField(blank=True)),
                ('session_notes', models.JSONField(blank=True, default=list)),
                ('products_used', models.JSONField(blank=True, default=list)),
                ('recommended_to_patient', models.JSONField(blank=True, default=list)),
                ('next_treatment', models.CharField(blank=True, max_length=255)),
                ('before_photo', models.TextField(blank=True)),
                ('after_photo', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_notes', to='patients.patient')),
                ('appointment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='session_note', to='appointments.appointment')),
                ('therapist', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='session_notes', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]