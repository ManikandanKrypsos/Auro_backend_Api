from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treatments', '0007_fix_room_type_nullable'),
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='rooms',
            field=models.ManyToManyField(blank=True, related_name='treatments', to='rooms.room'),
        ),
    ]