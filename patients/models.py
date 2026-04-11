from django.db import models

class Patient(models.Model):
    CATEGORY_CHOICES = (
        ('New', 'New'),
        ('Returning', 'Returning'),
        ('VIP', 'VIP'),
        ('Lead', 'Lead'),
    )

    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    # Basic info
    name              = models.CharField(max_length=100)
    phone             = models.CharField(max_length=15)
    email             = models.EmailField(blank=True, null=True)
    image             = models.URLField(blank=True)

    # Personal details
    city              = models.CharField(max_length=100, blank=True)
    country           = models.CharField(max_length=100, blank=True)
    gender            = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    dob               = models.DateField(null=True, blank=True)
    blood_type        = models.CharField(max_length=10, blank=True)

    # Medical info
    skin_type         = models.CharField(max_length=50, blank=True)
    allergies         = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    notes             = models.TextField(blank=True)

    # CRM
    category          = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='New')
    marketing_source  = models.CharField(max_length=100, blank=True)
    tags              = models.CharField(max_length=100, blank=True)

    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name