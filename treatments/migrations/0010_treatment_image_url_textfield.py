from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0009_fix_room_types_nullable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='treatment',
            name='image_url',
            field=models.TextField(blank=True),
        ),
    ]