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


class Equipment(models.Model):
    """
    One physical machine the clinic owns (Venus laser, Dermapen, ...). A treatment can require one;
    two appointments needing the same machine can't overlap.
    """
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                               related_name='equipment')   # set automatically from the logged-in user
    objects = TenantManager()

    STATUS_CHOICES = [
        ('active',      'Active'),
        ('maintenance', 'In maintenance'),
        ('retired',     'Retired'),
    ]

    name          = models.CharField(max_length=100)
    model         = models.CharField(max_length=100, blank=True)      # make / model, e.g. "Venus Legacy"
    serial_number = models.CharField(max_length=100, blank=True)
    room          = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='equipment')       # where it usually lives (info only)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['clinic', 'name'], name='equipment_name_unique_per_clinic')]

    def __str__(self):
        return self.name