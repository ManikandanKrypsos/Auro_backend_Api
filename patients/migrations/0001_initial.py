from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_id', models.CharField(blank=True, max_length=20, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=15)),
                ('email', models.EmailField(blank=True, null=True)),
                ('image', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('gender', models.CharField(blank=True, choices=[('Female','Female'),('Male','Male'),('Other','Other')], max_length=20)),
                ('dob', models.DateField(blank=True, null=True)),
                ('blood_type', models.CharField(blank=True, choices=[('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')], max_length=10)),
                ('allergies', models.TextField(blank=True)),
                ('skin_type', models.CharField(blank=True, choices=[('Normal','Normal'),('Dry','Dry'),('Oily','Oily'),('Combination','Combination'),('Sensitive','Sensitive')], max_length=50)),
                ('contraindications', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('category', models.CharField(choices=[('New','New'),('Returning','Returning'),('VIP','VIP'),('Lead','Lead')], default='New', max_length=20)),
                ('marketing_source', models.IntegerField(blank=True, choices=[(1,'Instagram'),(2,'Website'),(3,'Walk-in'),(4,'Referral'),(5,'WhatsApp'),(6,'Other')], default=None, null=True)),
                ('tags', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ConsentRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('file_name', models.CharField(blank=True, max_length=255)),
                ('file_url', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('signed','Signed'),('pending','Pending')], default='pending', max_length=10)),
                ('patient_signed', models.BooleanField(default=False)),
                ('therapist_signed', models.BooleanField(default=False)),
                ('signed_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consent_records', to='patients.patient')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]