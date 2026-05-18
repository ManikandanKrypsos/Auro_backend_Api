import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('username', models.CharField(blank=True, max_length=150)),
                ('role', models.CharField(blank=True, choices=[('admin','Admin'),('reception','Receptionist'),('therapist','Therapist')], max_length=20)),
                ('profile_image', models.TextField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('specialist_area', models.CharField(blank=True, max_length=100)),
                ('joining_date', models.DateField(blank=True, null=True)),
                ('years_of_experience', models.FloatField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', to='auth.permission')),
            ],
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'abstract': False},
            managers=[('objects', django.contrib.auth.models.UserManager())],
        ),
        migrations.CreateModel(
            name='StaffWorkingHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('Mon','Monday'),('Tue','Tuesday'),('Wed','Wednesday'),('Thu','Thursday'),('Fri','Friday'),('Sat','Saturday'),('Sun','Sunday')], max_length=3)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='working_hours', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['staff', 'day'], 'unique_together': {('staff', 'day')}},
        ),
        migrations.CreateModel(
            name='StaffBreakTime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('label', models.CharField(blank=True, max_length=100)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='break_times', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['staff', 'start_time']},
        ),
        migrations.CreateModel(
            name='StaffLeave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('reason', models.TextField(blank=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaves', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['staff', 'from_date']},
        ),
    ]