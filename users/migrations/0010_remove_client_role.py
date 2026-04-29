from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_user_years_of_experience'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                blank=True,
                choices=[
                    ('admin',     'Admin'),
                    ('reception', 'Receptionist'),
                    ('therapist', 'Therapist'),
                ],
                max_length=20,
            ),
        ),
    ]