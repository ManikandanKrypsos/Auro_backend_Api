from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0006_add_insession_status'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    -- Rename therapist_id to staff_id if it exists
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'appointments_appointment'
                        AND column_name = 'therapist_id'
                    ) THEN
                        ALTER TABLE appointments_appointment
                        RENAME COLUMN therapist_id TO staff_id;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'appointments_appointment'
                        AND column_name = 'staff_id'
                    ) THEN
                        ALTER TABLE appointments_appointment
                        RENAME COLUMN staff_id TO therapist_id;
                    END IF;
                END $$;
            """,
        ),
    ]