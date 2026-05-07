import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0005_patient_patient_id'),
        ('appointments', '0004_update_payment_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS patients_sessionnote (
                    id BIGSERIAL PRIMARY KEY,
                    treatment_name VARCHAR(150) NOT NULL DEFAULT '',
                    skin_observation TEXT NOT NULL DEFAULT '',
                    advice_given TEXT NOT NULL DEFAULT '',
                    products_used JSONB NOT NULL DEFAULT '[]',
                    recommended_to_patient JSONB NOT NULL DEFAULT '[]',
                    next_treatment VARCHAR(255) NOT NULL DEFAULT '',
                    before_photo TEXT NOT NULL DEFAULT '',
                    after_photo TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    patient_id BIGINT NOT NULL REFERENCES patients_patient(id) ON DELETE CASCADE,
                    therapist_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
                    appointment_id BIGINT UNIQUE REFERENCES appointments_appointment(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS patients_consentrecord (
                    id BIGSERIAL PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    file_name VARCHAR(255) NOT NULL DEFAULT '',
                    file_url TEXT NOT NULL DEFAULT '',
                    status VARCHAR(10) NOT NULL DEFAULT 'pending',
                    patient_signed BOOLEAN NOT NULL DEFAULT FALSE,
                    therapist_signed BOOLEAN NOT NULL DEFAULT FALSE,
                    signed_date DATE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    patient_id BIGINT NOT NULL REFERENCES patients_patient(id) ON DELETE CASCADE
                );
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS patients_consentrecord;
                DROP TABLE IF EXISTS patients_sessionnote;
            """,
        ),
    ]