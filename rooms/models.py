from django.db import models

from tenants.managers import TenantManager


class Room(models.Model):
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                               related_name='rooms')   # set automatically from the logged-in user
    objects = TenantManager()                 # every query is scoped to the current clinic

    ROOM_TYPE_CHOICES = [
        ('facial_treatment', 'Facial Treatment Room'),
        ('body_treatment',   'Body Treatment Room'),
    ]

    name        = models.CharField(max_length=100)
    room_type   = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['clinic', 'name'], name='room_name_unique_per_clinic')]

    def __str__(self):
        return f"{self.name} ({self.room_type})"