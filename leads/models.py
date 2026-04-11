from django.db import models
from users.models import User

class Lead(models.Model):
    SOURCE_CHOICES = (
        ('instagram', 'Instagram'),
        ('website', 'Website'),
        ('walkin', 'Walk-in'),
        ('referral', 'Referral'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Other'),
    )

    STAGE_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('consultation', 'Consultation'),
        ('converted', 'Converted'),   # 👈 changed from 'booked' to match Flutter
        ('lost', 'Lost'),
        ('returning', 'Returning'),
        ('vip', 'VIP'),
    )

    name            = models.CharField(max_length=100)
    phone           = models.CharField(max_length=15)
    email           = models.EmailField(blank=True, null=True)
    source          = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='instagram')
    stage           = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    interest        = models.CharField(max_length=100, blank=True)  # 👈 new — e.g. "Signature Facial"
    notes           = models.TextField(blank=True)
    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    score           = models.IntegerField(default=0)
    last_contacted  = models.DateField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} — {self.stage}"


class LeadActivity(models.Model):
    ACTION_CHOICES = (
        ('call', 'Call'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('stage_change', 'Stage Change'),
        ('note', 'Note'),
    )

    lead        = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    note        = models.TextField(blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.name} — {self.action} at {self.created_at}"