from django.db import migrations, models


def merge_winning(apps, schema_editor):
    """Every lead in the old 'winning' stage becomes 'converted' (Won)."""
    Lead = apps.get_model('leads', 'Lead')
    Lead.objects.filter(stage='winning').update(stage='converted')


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0003_lead_next_action_date'),
    ]

    operations = [
        migrations.RunPython(merge_winning, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='lead',
            name='stage',
            field=models.CharField(
                choices=[('new_inquiries', 'New'), ('engaged', 'Contacted'), ('consultation', 'Consultation'),
                         ('converted', 'Won'), ('lost', 'Lost')],
                default='new_inquiries', max_length=20),
        ),
    ]
