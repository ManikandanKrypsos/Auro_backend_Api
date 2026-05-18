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
            name='Lead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(blank=True, null=True)),
                ('source', models.CharField(choices=[('instagram','Instagram'),('web','Web'),('walk_in','Walk-In'),('referral','Referral'),('whatsapp','WhatsApp'),('other','Other')], default='web', max_length=20)),
                ('stage', models.CharField(choices=[('new_inquiries','New Inquiries'),('engaged','Engaged'),('consultation','Consultation'),('winning','Winning'),('converted','Converted'),('lost','Lost')], default='new_inquiries', max_length=20)),
                ('interest', models.CharField(blank=True, max_length=100)),
                ('service_id', models.IntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('value', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('last_contacted', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leads', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='LeadActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('call','Call'),('whatsapp','WhatsApp'),('email','Email'),('meeting','Meeting'),('stage_change','Stage Change'),('note','Note')], max_length=20)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='leads.lead')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]