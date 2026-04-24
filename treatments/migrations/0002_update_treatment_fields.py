import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add new fields
        migrations.AddField(
            model_name='treatment',
            name='category',
            field=models.CharField(choices=[('face','Face'),('body','Body')], default='face', max_length=10),
        ),
        migrations.AddField(
            model_name='treatment',
            name='image_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='treatment',
            name='pre_care_instructions',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='treatment',
            name='post_care_instructions',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='treatment',
            name='contraindications',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='treatment',
            name='room_type',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='treatment',
            name='staff',
            field=models.ManyToManyField(blank=True, limit_choices_to={'role__in': ['therapist', 'reception']}, related_name='treatments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='treatment',
            name='recommended_frequency_value',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='treatment',
            name='recommended_frequency_unit',
            field=models.CharField(blank=True, choices=[('days','Days'),('weeks','Weeks'),('months','Months')], max_length=10),
        ),
        migrations.AddField(
            model_name='treatment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='treatment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Rename old fields
        migrations.RenameField(
            model_name='treatment',
            old_name='pre_care',
            new_name='pre_care_old',
        ),
        migrations.RenameField(
            model_name='treatment',
            old_name='post_care',
            new_name='post_care_old',
        ),
        # Create PricePlan model
        migrations.CreateModel(
            name='PricePlan',
            fields=[
                ('id',        models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('sessions',  models.PositiveIntegerField()),
                ('price',     models.DecimalField(decimal_places=2, max_digits=10)),
                ('treatment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_plans', to='treatments.treatment')),
            ],
            options={'ordering': ['sessions']},
        ),
    ]