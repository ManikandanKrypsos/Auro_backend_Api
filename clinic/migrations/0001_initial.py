from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ClinicHours',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('day',        models.CharField(choices=[('Mon','Monday'),('Tue','Tuesday'),('Wed','Wednesday'),('Thu','Thursday'),('Fri','Friday'),('Sat','Saturday'),('Sun','Sunday')], max_length=3, unique=True)),
                ('is_open',    models.BooleanField(default=False)),
                ('open_time',  models.TimeField(blank=True, null=True)),
                ('close_time', models.TimeField(blank=True, null=True)),
            ],
            options={'ordering': ['id']},
        ),
        migrations.CreateModel(
            name='PlannedClosure',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('from_date',  models.DateField()),
                ('to_date',    models.DateField()),
                ('reason',     models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['from_date']},
        ),
    ]