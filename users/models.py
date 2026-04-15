from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin',      'Admin'),
        ('reception',  'Receptionist'),
        ('therapist',  'Therapist'),
        ('client',     'Client'),
    )

    # Make email unique and required
    email    = models.EmailField(unique=True)
    role     = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)

    # Make username not required
    username = models.CharField(max_length=150, blank=True, unique=False)

    USERNAME_FIELD  = 'email'        # 👈 login with email
    REQUIRED_FIELDS = []             # 👈 no extra required fields

    def __str__(self):
        return self.email