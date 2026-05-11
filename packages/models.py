from django.db import models
from patients.models import Patient
from treatments.models import Treatment, PricePlan


class PatientPackage(models.Model):

    STATUS_CHOICES = (
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_TYPE_CHOICES = (
        ('online', 'Online Payment'),
        ('cash',   'Cash'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid',    'Paid'),
        ('refunded','Refunded'),
    )

    patient       = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='packages')
    treatment     = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='packages')
    price_plan    = models.ForeignKey(PricePlan, on_delete=models.CASCADE, related_name='packages')
    total_sessions     = models.PositiveIntegerField()
    sessions_completed = models.PositiveIntegerField(default=0)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type  = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    @property
    def sessions_remaining(self):
        return max(self.total_sessions - self.sessions_completed, 0)

    @property
    def status_id(self):
        return {'active': 1, 'completed': 2, 'cancelled': 3}.get(self.status, 1)

    @property
    def payment_type_id(self):
        return {'online': 1, 'cash': 2}.get(self.payment_type)

    @property
    def payment_status_id(self):
        return {'pending': 1, 'paid': 2, 'refunded': 3}.get(self.payment_status)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.name} — {self.treatment.name} ({self.sessions_completed}/{self.total_sessions})"