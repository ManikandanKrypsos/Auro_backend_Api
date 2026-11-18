from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Clinic(models.Model):
    STATUS_CHOICES = (('active', 'Active'), ('suspended', 'Suspended'))

    name             = models.CharField(max_length=150)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    suspended_at     = models.DateTimeField(null=True, blank=True)
    suspended_reason = models.CharField(max_length=255, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.status == 'active'


class PlatformAdmin(models.Model):
    """Super Admin of the SaaS platform — not a clinic user, has its own login."""
    name       = models.CharField(max_length=150)
    email      = models.EmailField(unique=True)
    password   = models.CharField(max_length=128)
    is_active  = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return check_password(raw, self.password)

    def __str__(self):
        return self.email
