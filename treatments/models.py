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
    equipment = models.ForeignKey('rooms.Equipment', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='treatments')   # machine this treatment needs (booking conflicts)

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


class SessionConsumption(models.Model):
    """
    The therapist's confirmed product usage for one appointment — the only thing that takes
    consumables out of stock (see treatments.consumption). The treatment's consumables only
    pre-fill it. Editing it puts the previous usage back and records the new one; if the
    appointment stops being in session / completed, it is reversed.
    """
    objects      = TenantManager.via('appointment__clinic_id')()

    appointment  = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE, related_name='consumption_records')
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    note         = models.CharField(max_length=255, blank=True)
    # admin review of what the therapist confirmed (a new confirmation starts unreviewed)
    reviewed     = models.BooleanField(default=False)
    reviewed_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reviewed_at  = models.DateTimeField(null=True, blank=True)
    review_note  = models.CharField(max_length=500, blank=True)
    reversed     = models.BooleanField(default=False)
    reversed_at  = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']


class AppointmentConsumption(models.Model):
    """One item of a confirmed SessionConsumption."""
    objects     = TenantManager.via('record__appointment__clinic_id')()

    TYPE_CHOICES = [
        ('used',     'Used in the treatment'),          # deducted from stock ('used' movement)
        ('waste',    'Wasted / broken'),                # deducted from stock ('wastage' movement)
        ('returned', 'Returned to stock unused'),       # not deducted — recorded for traceability
    ]

    record      = models.ForeignKey(SessionConsumption, on_delete=models.CASCADE, related_name='lines')
    item        = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE, related_name='+')
    type        = models.CharField(max_length=10, choices=TYPE_CHOICES, default='used')
    planned     = models.PositiveIntegerField(default=0)            # from the treatment's consumables (0 = extra item)
    quantity    = models.PositiveIntegerField()                     # what the therapist says was used
    deducted    = models.PositiveIntegerField(default=0)            # actually taken from stock
    shortfall   = models.PositiveIntegerField(default=0)            # used but not in stock
    lot         = models.ForeignKey('inventory.Lot', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    unit_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # item cost at the time
    movement    = models.ForeignKey('inventory.StockMovement', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='+')               # first movement it made (one per lot)

    class Meta:
        ordering = ['id']