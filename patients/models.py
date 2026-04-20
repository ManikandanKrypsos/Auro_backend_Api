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

    # 👈 Custom patient ID
    patient_id        = models.CharField(max_length=20, unique=True, blank=True)

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
    marketing_source  = models.IntegerField(
                            choices=MARKETING_SOURCE_CHOICES,
                            null=True, blank=True, default=None
                        )
    tags              = models.CharField(max_length=100, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate patient_id like Aura1, Aura2...
        if not self.patient_id:
            super().save(*args, **kwargs)  # save first to get auto id
            self.patient_id = f'Aura{self.id}'
            Patient.objects.filter(id=self.id).update(patient_id=self.patient_id)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.patient_id} — {self.name}'
        