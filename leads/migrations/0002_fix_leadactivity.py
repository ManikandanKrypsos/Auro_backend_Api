from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('leads', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS leads_leadactivity;
                CREATE TABLE leads_leadactivity (
                    id BIGSERIAL PRIMARY KEY,
                    lead_id BIGINT NOT NULL REFERENCES leads_lead(id) ON DELETE CASCADE,
                    action VARCHAR(20) NOT NULL DEFAULT 'note',
                    note TEXT NOT NULL DEFAULT '',
                    created_by_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS leads_leadactivity;",
        ),
    ]