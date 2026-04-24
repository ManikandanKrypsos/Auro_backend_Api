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
                ('room_type',   models.CharField(choices=[('facial_treatment','Facial Treatment Room'),('body_treatment','Body Treatment Room')], max_length=50)),
                ('description', models.TextField(blank=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
    ]