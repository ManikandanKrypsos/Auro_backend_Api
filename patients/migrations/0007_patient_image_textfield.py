from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0006_sessionnote_consentrecord'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='image',
            field=models.TextField(blank=True),
        ),
    ]