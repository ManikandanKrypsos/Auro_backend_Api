import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0006_add_insession_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    -- If therapist_id exists, rename to staff_id
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'appointments_appointment'
                        AND column_name = 'therapist_id'
                    ) THEN
                        ALTER TABLE appointments_appointment
                        RENAME COLUMN therapist_id TO staff_id;

                    -- If neither exists, add staff_id column
                    ELSIF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'appointments_appointment'
                        AND column_name = 'staff_id'
                    ) THEN
                        ALTER TABLE appointments_appointment
                        ADD COLUMN staff_id BIGINT REFERENCES users_user(id);
                    END IF;
                END $$;
            """,
            reverse_sql="SELECT 1;",
        ),
    ]