from django.db import models
from users.models import User


class Lead(models.Model):
    SOURCE_CHOICES = (
        ('instagram',  'Instagram'),
        ('web',        'Web'),
        ('walk_in',    'Walk-In'),
        ('referral',   'Referral'),
        ('whatsapp',   'WhatsApp'),
        ('other',      'Other'),
    )

    STAGE_CHOICES = (
        ('new_inquiries', 'New Inquiries'),
        ('engaged',       'Engaged'),
        ('consultation',  'Consultation'),
        ('winning',       'Winning'),
        ('converted',     'Converted'),
        ('lost',          'Lost'),
    )

    name           = models.CharField(max_length=100)
    phone          = models.CharField(max_length=20)
    email          = models.EmailField(blank=True, null=True)
    source         = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='web')
    stage          = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new_inquiries')
    interest       = models.CharField(max_length=100, blank=True)  # legacy text field
    service_id     = models.IntegerField(null=True, blank=True)    # treatment/service FK
    notes          = models.TextField(blank=True)
    assigned_to    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    value          = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # estimated value
    last_contacted = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.stage}"


class LeadActivity(models.Model):
    ACTION_CHOICES = (
        ('call',         'Call'),
        ('whatsapp',     'WhatsApp'),
        ('email',        'Email'),
        ('meeting',      'Meeting'),
        ('stage_change', 'Stage Change'),
        ('note',         'Note'),
    )

    lead       = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    note       = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lead.name} — {self.action}"