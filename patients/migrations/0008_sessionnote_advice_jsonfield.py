from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0007_patient_image_textfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessionnote',
            name='advice_given',
            field=models.JSONField(blank=True, default=list),
        ),
    ]