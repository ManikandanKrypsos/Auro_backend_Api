from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin',     'Admin'),
        ('reception', 'Receptionist'),
        ('therapist', 'Therapist'),
        ('client',    'Client'),
    )

    email    = models.EmailField(unique=True)          
    username = models.CharField(max_length=150, blank=True)  
    role     = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)

    USERNAME_FIELD  = 'email'    
    REQUIRED_FIELDS = []         

    class Meta:
        constraints = []         

    def __str__(self):
        return self.email