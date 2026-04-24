from django.db import models
from users.models import User


class Treatment(models.Model):
    CATEGORY_CHOICES = [
        ('face', 'Face'),
        ('body', 'Body'),
    ]

    FREQUENCY_UNIT_CHOICES = [
        ('days',   'Days'),
        ('weeks',  'Weeks'),
        ('months', 'Months'),
    ]

    # ── Basic Info ────────────────────────────────────────────────
    name        = models.CharField(max_length=100)
    category    = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='face')
    description = models.TextField(blank=True)
    duration    = models.PositiveIntegerField(help_text="Duration in minutes")
    image_url   = models.URLField(max_length=500, blank=True)

    # ── Price Plans ───────────────────────────────────────────────
    # Stored as related PricePlan objects below

    # ── Treatment Protocol ────────────────────────────────────────
    pre_care_instructions  = models.TextField(blank=True)
    post_care_instructions = models.TextField(blank=True)
    contraindications      = models.JSONField(default=list, blank=True)

    # ── Resources ─────────────────────────────────────────────────
    room_type   = models.CharField(max_length=50, blank=True)  # facial_treatment / body_treatment

    # ── Staff Assignment ──────────────────────────────────────────
    staff       = models.ManyToManyField(
        User, blank=True, related_name='treatments',
        limit_choices_to={'role__in': ['therapist', 'reception']}
    )

    # ── Advanced Settings ─────────────────────────────────────────
    recommended_frequency_value = models.PositiveIntegerField(null=True, blank=True)
    recommended_frequency_unit  = models.CharField(
        max_length=10, choices=FREQUENCY_UNIT_CHOICES, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PricePlan(models.Model):
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='price_plans')
    sessions  = models.PositiveIntegerField()
    price     = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['sessions']

    def __str__(self):
        return f"{self.treatment.name} — {self.sessions} session(s) @ {self.price}"