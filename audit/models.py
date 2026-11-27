from django.conf import settings
from django.db import models

from tenants.managers import TenantManager


class AuditEvent(models.Model):
    """
    One thing someone did: who, what, to which record, and the values before / after.
    Written by audit.recorder (signals) — never edited or deleted through the API.
    """
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    objects = TenantManager()

    CATEGORY_CHOICES = (('clinical', 'Clinical'), ('financial', 'Financial'), ('stock', 'Stock'))
    SOURCE_CHOICES = (('live', 'Recorded when it happened'), ('backfill', 'Rebuilt from existing records'))

    category     = models.CharField(max_length=12, choices=CATEGORY_CHOICES, db_index=True)
    action       = models.CharField(max_length=40, db_index=True)
    summary      = models.CharField(max_length=255, blank=True)
    actor        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='+')
    actor_label  = models.CharField(max_length=150, blank=True)      # name at the time (kept if the user is deleted)
    actor_role   = models.CharField(max_length=20, blank=True)
    target_type  = models.CharField(max_length=30, db_index=True)
    target_id    = models.CharField(max_length=40, db_index=True)
    target_label = models.CharField(max_length=255, blank=True)
    patient      = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='+')
    patient_label = models.CharField(max_length=150, blank=True)
    before       = models.JSONField(null=True, blank=True)
    after        = models.JSONField(null=True, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    request_id   = models.CharField(max_length=64, blank=True)
    source       = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='live')
    created_at   = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['clinic', 'category', '-created_at'], name='audit_clinic_cat_time')]
