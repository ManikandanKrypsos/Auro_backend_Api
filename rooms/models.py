from django.db import models


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('therapy_suite',     'Therapy Suite'),
        ('consultation',      'Consultation'),
        ('treatment_room',    'Treatment Room'),
        ('recovery_room',     'Recovery Room'),
        ('waiting_area',      'Waiting Area'),
    ]

    name        = models.CharField(max_length=100, unique=True)
    room_type   = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.room_type})"