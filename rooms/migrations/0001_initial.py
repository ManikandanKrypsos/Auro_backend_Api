from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name',        models.CharField(max_length=100, unique=True)),
                ('room_type',   models.CharField(choices=[('therapy_suite','Therapy Suite'),('consultation','Consultation'),('treatment_room','Treatment Room'),('recovery_room','Recovery Room'),('waiting_area','Waiting Area')], max_length=50)),
                ('description', models.TextField(blank=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
    ]