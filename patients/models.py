from django.db import models

MARKETING_SOURCE_CHOICES = (
    (1, 'Instagram'),
    (2, 'Website'),
    (3, 'Walk-in'),
    (4, 'Referral'),
    (5, 'WhatsApp'),
    (6, 'Other'),
)

class Patient(models.Model):
    CATEGORY_CHOICES = (
        ('New', 'New'),
        ('Returning', 'Returning'),
        ('VIP', 'VIP'),
        ('Lead', 'Lead'),
    )
    GENDER_CHOICES = (
        ('Female', 'Female'),
        ('Male', 'Male'),
        ('Other', 'Other'),
    )
    SKIN_TYPE_CHOICES = (
        ('Normal', 'Normal'),
        ('Dry', 'Dry'),
        ('Oily', 'Oily'),
        ('Combination', 'Combination'),
        ('Sensitive', 'Sensitive'),
    )
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )

    # Basic info
    name              = models.CharField(max_length=100)
    phone             = models.CharField(max_length=15)
    email             = models.EmailField(blank=True, null=True)
    image             = models.URLField(blank=True)

    # Address
    city              = models.CharField(max_length=100, blank=True)
    country           = models.CharField(max_length=100, blank=True)

    # Basic info
    gender            = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    dob               = models.DateField(null=True, blank=True)

    # Medical
    blood_type        = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, blank=True)
    allergies         = models.TextField(blank=True)
    skin_type         = models.CharField(max_length=50, choices=SKIN_TYPE_CHOICES, blank=True)
    contraindications = models.TextField(blank=True)
    notes             = models.TextField(blank=True)

    # CRM
    category          = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='New')
    marketing_source  = models.IntegerField(   # 👈 now integer ID like role
                            choices=MARKETING_SOURCE_CHOICES,
                            null=True, blank=True
                        )
    tags              = models.CharField(max_length=100, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name