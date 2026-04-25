from django.db import models


class ClinicHours(models.Model):
    DAY_CHOICES = [
        ('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday'),
    ]

    day        = models.CharField(max_length=3, choices=DAY_CHOICES, unique=True)
    is_open    = models.BooleanField(default=False)
    open_time  = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.day} — {'Open' if self.is_open else 'Closed'}"


class PlannedClosure(models.Model):
    from_date  = models.DateField()
    to_date    = models.DateField()
    reason     = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['from_date']

    def __str__(self):
        return f"Closure {self.from_date} to {self.to_date}"