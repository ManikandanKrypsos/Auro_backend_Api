from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenants'
    verbose_name = 'Clinics (tenancy)'

    def ready(self):
        from . import signals  # noqa: F401  (auto-assigns clinic on save)
