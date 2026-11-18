from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from tenants.managers import TenantManager, TenantUserManager

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin',     'Admin'),
        ('reception', 'Receptionist'),
        ('therapist', 'Therapist'),
    )

    email              = models.EmailField(unique=True)
    username           = models.CharField(max_length=150, blank=True)
    role               = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)
    clinic             = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                                           related_name='users')
    must_change_password = models.BooleanField(default=False)   # set for staff created with a temp password

    objects     = TenantUserManager()   # scoped to the logged-in user's clinic
    all_objects = UserManager()         # unscoped: login, email uniqueness, platform admin

    # Staff profile fields (used for reception & therapist)
    profile_image      = models.TextField(blank=True)  # stores URL or base64 image
    phone              = models.CharField(max_length=30, blank=True)
    specialist_area    = models.CharField(max_length=100, blank=True)
    joining_date       = models.DateField(null=True, blank=True)
    years_of_experience = models.FloatField(null=True, blank=True)

    USERNAME_FIELD  = 'email'    
    REQUIRED_FIELDS = []         

    class Meta:
        constraints = []
        default_manager_name = 'objects'

    def __str__(self):
        return self.email

# ─── Staff Schedule Models ────────────────────────────────────────────────────

class StaffWorkingHours(models.Model):
    objects = TenantManager.via('staff__clinic_id')()   # scoped to the current clinic via its parent

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
    objects = TenantManager.via('staff__clinic_id')()   # scoped to the current clinic via its parent

    staff      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='break_times')
    start_time = models.TimeField()
    end_time   = models.TimeField()
    label      = models.CharField(max_length=100, blank=True)   # e.g. "Lunch", "Prayer"

    class Meta:
        ordering = ['staff', 'start_time']

    def __str__(self):
        return f"{self.staff.username} break {self.start_time}–{self.end_time}"


class StaffLeave(models.Model):
    objects = TenantManager.via('staff__clinic_id')()   # scoped to the current clinic via its parent

    staff      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    from_date  = models.DateField()
    to_date    = models.DateField()
    reason     = models.TextField(blank=True)

    class Meta:
        ordering = ['staff', 'from_date']

    def __str__(self):
        return f"{self.staff.username} leave {self.from_date}–{self.to_date}"