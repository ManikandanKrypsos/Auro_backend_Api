from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_user_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='years_of_experience',
            field=models.FloatField(blank=True, null=True),
        ),
    ]