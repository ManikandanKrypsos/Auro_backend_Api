"""
Managers that scope every query to the current request's clinic.
`tenant_path` is the lookup to the clinic id: 'clinic_id' for tables that carry it,
or e.g. 'staff__clinic_id' for child tables that belong to a parent row.
"""
from django.contrib.auth.models import UserManager
from django.db import models

from .context import get_current_clinic_id


class TenantManager(models.Manager):
    """
    Scoped to the current clinic through `tenant_path` (a class attribute, so the related
    managers Django builds by subclassing keep the same scoping). Use TenantManager() for
    tables with a clinic column, TenantManager.via('staff__clinic_id')() for child tables.
    """
    tenant_path = 'clinic_id'

    @classmethod
    def via(cls, path):
        return type(f'TenantManagerVia_{path.replace("__", "_")}', (cls,), {'tenant_path': path})

    def get_queryset(self):
        qs = super().get_queryset()
        clinic_id = get_current_clinic_id()
        if clinic_id is not None:
            qs = qs.filter(**{self.tenant_path: clinic_id})
        return qs


class TenantUserManager(UserManager):
    """User manager scoped to the current clinic (create_user etc. still work)."""
    use_in_migrations = False

    def get_queryset(self):
        qs = super().get_queryset()
        clinic_id = get_current_clinic_id()
        if clinic_id is not None:
            qs = qs.filter(clinic_id=clinic_id)
        return qs
