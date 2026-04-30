from django.db import models
from users.models import User
from patients.models import Patient
from treatments.models import Treatment, PricePlan
from rooms.models import Room


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('upcoming',   'Upcoming'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
        ('no_show',    'No Show'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending',  'Pending'),
        ('paid',     'Paid'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_TYPE_CHOICES = (
        ('single',  'Single'),
        ('package', 'Package'),
    )

    CONSENT_STATUS_CHOICES = (
        ('pending',  'Pending'),
        ('signed',   'Signed'),
    )

    # Core
    patient         = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    staff           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    treatment       = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='appointments')
    room_fk         = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments', db_column='room_fk_id')
    price_plan      = models.ForeignKey(PricePlan, on_delete=models.SET_NULL, null=True, blank=True)

    # Scheduling
    date_time       = models.DateTimeField()
    duration        = models.PositiveIntegerField(help_text="Duration in minutes", default=60)

    # Session tracking (for packages)
    session_number  = models.PositiveIntegerField(default=1)
    total_sessions  = models.PositiveIntegerField(default=1)

    # Status
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    patient_arrived = models.BooleanField(default=False)

    # Consent
    consent_status  = models.CharField(max_length=20, choices=CONSENT_STATUS_CHOICES, default='pending')
    consent_form_url = models.URLField(blank=True)

    # Payment
    payment_amount  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status  = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_type    = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='single')

    # Notes
    notes           = models.TextField(blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date_time']

    def __str__(self):
        return f"{self.patient.name} — {self.treatment.name} @ {self.date_time}"