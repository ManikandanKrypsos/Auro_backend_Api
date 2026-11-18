from django.db import models

from tenants.managers import TenantManager


class ClinicHours(models.Model):
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                               related_name='opening_hours')   # set automatically from the logged-in user
    objects = TenantManager()                 # every query is scoped to the current clinic

    DAY_CHOICES = [
        ('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday'),
    ]

    day        = models.CharField(max_length=3, choices=DAY_CHOICES)
    is_open    = models.BooleanField(default=False)
    open_time  = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']
        constraints = [models.UniqueConstraint(fields=['clinic', 'day'], name='clinic_hours_day_unique_per_clinic')]

    def __str__(self):
        return f"{self.day} — {'Open' if self.is_open else 'Closed'}"


class PlannedClosure(models.Model):
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                               related_name='planned_closures')   # set automatically from the logged-in user
    objects = TenantManager()                 # every query is scoped to the current clinic

    from_date  = models.DateField()
    to_date    = models.DateField()
    reason     = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['from_date']

    def __str__(self):
        return f"Closure {self.from_date} to {self.to_date}"