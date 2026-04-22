# Adds StaffWorkingHours, StaffBreakTime, StaffLeave models.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_staff_profile_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffWorkingHours',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('day',        models.CharField(choices=[('Mon','Monday'),('Tue','Tuesday'),('Wed','Wednesday'),('Thu','Thursday'),('Fri','Friday'),('Sat','Saturday'),('Sun','Sunday')], max_length=3)),
                ('start_time', models.TimeField()),
                ('end_time',   models.TimeField()),
                ('staff',      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='working_hours', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['staff', 'day']},
        ),
        migrations.AddConstraint(
            model_name='staffworkinghours',
            constraint=models.UniqueConstraint(fields=['staff', 'day'], name='unique_staff_day'),
        ),
        migrations.CreateModel(
            name='StaffBreakTime',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('start_time', models.TimeField()),
                ('end_time',   models.TimeField()),
                ('label',      models.CharField(blank=True, max_length=100)),
                ('staff',      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='break_times', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['staff', 'start_time']},
        ),
        migrations.CreateModel(
            name='StaffLeave',
            fields=[
                ('id',        models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('from_date', models.DateField()),
                ('to_date',   models.DateField()),
                ('reason',    models.TextField(blank=True)),
                ('staff',     models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaves', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['staff', 'from_date']},
        ),
    ]