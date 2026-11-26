from django.db import models

from tenants.managers import TenantManager
from patients.models import Patient
from treatments.models import Treatment, PricePlan


class PatientPackage(models.Model):
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                               related_name='patient_packages')   # set automatically from the logged-in user
    objects = TenantManager()                 # every query is scoped to the current clinic


    STATUS_CHOICES = (
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_TYPE_CHOICES = (
        ('online', 'Online Payment'),
        ('cash',   'Cash'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid',    'Paid'),
        ('refunded','Refunded'),
    )

    patient       = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='packages')
    treatment     = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='packages')
    price_plan    = models.ForeignKey(PricePlan, on_delete=models.CASCADE, related_name='packages')
    total_sessions     = models.PositiveIntegerField()
    sessions_completed = models.PositiveIntegerField(default=0)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type  = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    @property
    def sessions_remaining(self):
        return max(self.total_sessions - self.sessions_completed, 0)

    @property
    def status_id(self):
        return {'active': 1, 'completed': 2, 'cancelled': 3}.get(self.status, 1)

    @property
    def payment_type_id(self):
        return {'online': 1, 'cash': 2}.get(self.payment_type)

    @property
    def payment_status_id(self):
        return {'pending': 1, 'paid': 2, 'refunded': 3}.get(self.payment_status)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.name} — {self.treatment.name} ({self.sessions_completed}/{self.total_sessions})"

class TreatmentCourse(models.Model):
    """
    A patient's course of treatment: linked to their package, or just patient + treatment when there is
    no package. Holds the goal and progress, the pre-planned future sessions (PlannedSession) and the
    patient's own copy of the treatment protocol (copied from the service, then editable).
    """
    objects = TenantManager.via('patient__clinic_id')()

    STATUS_CHOICES = (
        ('active',    'Active'),
        ('paused',    'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    patient     = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='courses')
    treatment   = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='courses')
    package     = models.OneToOneField(PatientPackage, on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='course')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Goal + progress
    goal        = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)

    # Protocol instance (starts as a copy of the treatment's protocol)
    pre_care_instructions       = models.TextField(blank=True)
    post_care_instructions      = models.TextField(blank=True)
    contraindications           = models.JSONField(default=list, blank=True)
    recommended_frequency_value = models.PositiveIntegerField(null=True, blank=True)
    recommended_frequency_unit  = models.CharField(max_length=10, choices=Treatment.FREQUENCY_UNIT_CHOICES, blank=True)
    protocol_notes              = models.TextField(blank=True)    # anything specific to this patient

    created_by  = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    PROTOCOL_FIELDS = ('pre_care_instructions', 'post_care_instructions', 'contraindications',
                       'recommended_frequency_value', 'recommended_frequency_unit')

    class Meta:
        ordering = ['-created_at']

    def copy_protocol_from_treatment(self):
        for f in self.PROTOCOL_FIELDS:
            v = getattr(self.treatment, f)
            setattr(self, f, list(v or []) if f == 'contraindications' else (v if v is not None else (None if f.endswith('_value') else '')))

    def __str__(self):
        return f"{self.patient.name} — {self.treatment.name} course"


class CourseProgress(models.Model):
    """A progress entry towards the course goal (optionally tied to a session)."""
    objects = TenantManager.via('course__patient__clinic_id')()

    course       = models.ForeignKey(TreatmentCourse, on_delete=models.CASCADE, related_name='progress_entries')
    date         = models.DateField()
    progress_pct = models.PositiveSmallIntegerField(null=True, blank=True)    # 0–100, optional
    note         = models.TextField(blank=True)
    appointment  = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='+')
    created_by   = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']


class PlannedSession(models.Model):
    """'Session 4 of 6 is planned for <date>' — planned ahead; linked to the real appointment once booked."""
    objects = TenantManager.via('course__patient__clinic_id')()

    course         = models.ForeignKey(TreatmentCourse, on_delete=models.CASCADE, related_name='planned_sessions')
    session_number = models.PositiveIntegerField()
    planned_date   = models.DateField()
    planned_time   = models.TimeField(null=True, blank=True)
    staff          = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    notes          = models.TextField(blank=True)
    appointment    = models.OneToOneField('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='planned_session')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session_number']
        constraints = [models.UniqueConstraint(fields=['course', 'session_number'], name='planned_session_number_unique')]