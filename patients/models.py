from django.db import models
from django.conf import settings

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

    # Custom patient ID
    patient_id        = models.CharField(max_length=20, unique=True, blank=True)

    # Basic info
    name              = models.CharField(max_length=100)
    phone             = models.CharField(max_length=15)
    email             = models.EmailField(blank=True, null=True)
    image             = models.TextField(blank=True)  # stores URL or uploaded file path

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
        if not self.patient_id:
            super().save(*args, **kwargs)
            self.patient_id = f'Aura{self.id}'
            Patient.objects.filter(id=self.id).update(patient_id=self.patient_id)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.patient_id} — {self.name}'


# ── Session Notes ─────────────────────────────────────────────────────────────

class SessionNote(models.Model):
    patient                = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='session_notes')
    appointment            = models.OneToOneField(
                                'appointments.Appointment',
                                on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='session_note'
                             )
    therapist              = models.ForeignKey(
                                settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL,
                                null=True,
                                related_name='session_notes'
                             )
    treatment_name         = models.CharField(max_length=150, blank=True)
    skin_observation       = models.TextField(blank=True)
    advice_given           = models.TextField(blank=True)
    products_used          = models.JSONField(default=list, blank=True)
    recommended_to_patient = models.JSONField(default=list, blank=True)
    next_treatment         = models.CharField(max_length=255, blank=True)
    before_photo           = models.TextField(blank=True)
    after_photo            = models.TextField(blank=True)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.name} — {self.treatment_name}"


# ── Consent Records ───────────────────────────────────────────────────────────

class ConsentRecord(models.Model):
    STATUS_CHOICES = (
        ('signed',  'Signed'),
        ('pending', 'Pending'),
    )

    patient           = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consent_records')
    title             = models.CharField(max_length=150)
    file_name         = models.CharField(max_length=255, blank=True)
    file_url          = models.TextField(blank=True)
    status            = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    patient_signed    = models.BooleanField(default=False)
    therapist_signed  = models.BooleanField(default=False)
    signed_date       = models.DateField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.name} — {self.title} ({self.status})"