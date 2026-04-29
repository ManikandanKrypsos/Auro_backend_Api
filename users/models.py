from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin',     'Admin'),
        ('reception', 'Receptionist'),
        ('therapist', 'Therapist'),
    )

    email              = models.EmailField(unique=True)
    username           = models.CharField(max_length=150, blank=True)
    role               = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)

    # Staff profile fields (used for reception & therapist)
    profile_image      = models.URLField(max_length=500, blank=True)
    phone              = models.CharField(max_length=30, blank=True)
    specialist_area    = models.CharField(max_length=100, blank=True)
    joining_date       = models.DateField(null=True, blank=True)
    years_of_experience = models.FloatField(null=True, blank=True)

    USERNAME_FIELD  = 'email'    
    REQUIRED_FIELDS = []         

    class Meta:
        constraints = []         

    def __str__(self):
        return self.email

# ─── Staff Schedule Models ────────────────────────────────────────────────────

class StaffWorkingHours(models.Model):
    DAY_CHOICES = [
        ('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday'),
    ]

    staff      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='working_hours')
    day        = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time   = models.TimeField()

    class Meta:
        unique_together = ('staff', 'day')   # one schedule entry per day per staff
        ordering = ['staff', 'day']

    def __str__(self):
        return f"{self.staff.username} — {self.day} {self.start_time}–{self.end_time}"


class StaffBreakTime(models.Model):
    staff      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='break_times')
    start_time = models.TimeField()
    end_time   = models.TimeField()
    label      = models.CharField(max_length=100, blank=True)   # e.g. "Lunch", "Prayer"

    class Meta:
        ordering = ['staff', 'start_time']

    def __str__(self):
        return f"{self.staff.username} break {self.start_time}–{self.end_time}"


class StaffLeave(models.Model):
    staff      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    from_date  = models.DateField()
    to_date    = models.DateField()
    reason     = models.TextField(blank=True)

    class Meta:
        ordering = ['staff', 'from_date']

    def __str__(self):
        return f"{self.staff.username} leave {self.from_date}–{self.to_date}"