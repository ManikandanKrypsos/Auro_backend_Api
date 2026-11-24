from django.db import models

from tenants.managers import TenantManager
from users.models import User
from rooms.models import Room


class Treatment(models.Model):
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                               related_name='treatments')   # set automatically from the logged-in user
    objects = TenantManager()                 # every query is scoped to the current clinic

    CATEGORY_CHOICES = [
        ('face', 'Face'),
        ('body', 'Body'),
    ]

    FREQUENCY_UNIT_CHOICES = [
        ('days',   'Days'),
        ('weeks',  'Weeks'),
        ('months', 'Months'),
    ]

    # Basic Info
    name        = models.CharField(max_length=100)
    category    = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='face')
    description = models.TextField(blank=True)
    duration    = models.PositiveIntegerField(help_text="Duration in minutes")
    price       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url   = models.TextField(blank=True)  # stores URL or uploaded file path

    # Treatment Protocol
    pre_care_instructions  = models.TextField(blank=True)
    post_care_instructions = models.TextField(blank=True)
    contraindications      = models.JSONField(default=list, blank=True)

    # Resources
    rooms = models.ManyToManyField(Room, blank=True, related_name='treatments')

    # Staff Assignment
    staff = models.ManyToManyField(
        User, blank=True, related_name='treatments',
        limit_choices_to={'role__in': ['therapist', 'reception']}
    )

    # Advanced Settings
    recommended_frequency_value = models.PositiveIntegerField(null=True, blank=True)
    recommended_frequency_unit  = models.CharField(
        max_length=10, choices=FREQUENCY_UNIT_CHOICES, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PricePlan(models.Model):
    objects = TenantManager.via('treatment__clinic_id')()   # scoped to the current clinic via its parent

    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='price_plans')
    sessions  = models.PositiveIntegerField()
    price     = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['sessions']

    def __str__(self):
        return f"{self.treatment.name} — {self.sessions} session(s) @ {self.price}"

class TreatmentConsumable(models.Model):
    """An inventory item a treatment uses, and how many units per appointment."""
    objects   = TenantManager.via('treatment__clinic_id')()

    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='consumables')
    item      = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE, related_name='used_by_treatments')
    quantity  = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        constraints = [models.UniqueConstraint(fields=['treatment', 'item'], name='treatment_consumable_unique')]


class AppointmentConsumption(models.Model):
    """
    What completing an appointment took from stock, per item (see treatments.consumption).
    Rows stay as history; if the appointment stops being completed they are marked reversed and
    the stock is put back.
    """
    objects     = TenantManager.via('appointment__clinic_id')()

    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE, related_name='consumptions')
    item        = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE, related_name='+')
    planned     = models.PositiveIntegerField()                 # from the treatment's consumables
    deducted    = models.PositiveIntegerField(default=0)        # actually taken from stock
    shortfall   = models.PositiveIntegerField(default=0)        # planned but not in stock
    skipped_manual = models.BooleanField(default=False)         # already logged by hand for this appointment
    unit_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # item cost at the time
    movement    = models.ForeignKey('inventory.StockMovement', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='+')
    reversed    = models.BooleanField(default=False)
    reversal_movement = models.ForeignKey('inventory.StockMovement', on_delete=models.SET_NULL, null=True,
                                          blank=True, related_name='+')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']