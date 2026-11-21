from django.conf import settings
from django.db import models

from tenants.managers import TenantManager


class Notification(models.Model):
    """One in-app notification for one user (the bell icon)."""
    clinic     = models.ForeignKey('tenants.Clinic', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='notifications')
    objects    = TenantManager()

    recipient  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='notifications_caused')
    type       = models.CharField(max_length=40, db_index=True)
    message    = models.CharField(max_length=300)
    ref        = models.JSONField(default=dict, blank=True)   # ids of the related objects, e.g. {"leave_id": 12}
    is_read    = models.BooleanField(default=False)
    read_at    = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['recipient', 'is_read', '-created_at'], name='notif_recipient_unread')]


class NotificationPreference(models.Model):
    """A user's on/off choice for one notification type. No row = on."""
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_prefs')
    type    = models.CharField(max_length=40)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'type'], name='notif_pref_unique_per_user')]
