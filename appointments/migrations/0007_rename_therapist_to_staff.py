import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0006_add_insession_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Step 1: Add the column if it doesn't exist (handles fresh DB)
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'appointments_appointment'
                        AND column_name = 'therapist_id'
                    ) THEN
                        ALTER TABLE appointments_appointment
                        RENAME COLUMN therapist_id TO staff_id;
                    ELSIF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'appointments_appointment'
                        AND column_name = 'staff_id'
                    ) THEN
                        ALTER TABLE appointments_appointment
                        ADD COLUMN staff_id BIGINT REFERENCES users_user(id) ON DELETE CASCADE;
                    END IF;
                END $$;
            """,
            reverse_sql="SELECT 1;",
        ),
        # Step 2: Tell Django the field exists (fake state update)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='appointment',
                    name='staff',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='appointments',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            database_operations=[],  # DB already handled above
        ),
    ]