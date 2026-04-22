# Adds phone, specialist_area, joining_date, years_of_experience to User.
# NOTE: If these columns already exist in your DB, Django will skip the
# DB operations but still record this migration as applied.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_user_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='user',
            name='specialist_area',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='joining_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='years_of_experience',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]