from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('rooms', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Treatment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('category', models.CharField(choices=[('face','Face'),('body','Body')], default='face', max_length=10)),
                ('description', models.TextField(blank=True)),
                ('duration', models.PositiveIntegerField(help_text='Duration in minutes')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('image_url', models.TextField(blank=True)),
                ('pre_care_instructions', models.TextField(blank=True)),
                ('post_care_instructions', models.TextField(blank=True)),
                ('contraindications', models.JSONField(blank=True, default=list)),
                ('recommended_frequency_value', models.PositiveIntegerField(blank=True, null=True)),
                ('recommended_frequency_unit', models.CharField(blank=True, choices=[('days','Days'),('weeks','Weeks'),('months','Months')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rooms', models.ManyToManyField(blank=True, related_name='treatments', to='rooms.room')),
                ('staff', models.ManyToManyField(blank=True, limit_choices_to={'role__in': ['therapist', 'reception']}, related_name='treatments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PricePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sessions', models.PositiveIntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('treatment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_plans', to='treatments.treatment')),
            ],
            options={'ordering': ['sessions']},
        ),
    ]