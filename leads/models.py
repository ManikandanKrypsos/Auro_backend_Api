from django.db import models

from tenants.managers import TenantManager
from users.models import User


class Lead(models.Model):
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                               related_name='leads')   # set automatically from the logged-in user
    objects = TenantManager()                 # every query is scoped to the current clinic

    SOURCE_CHOICES = (
        ('instagram',  'Instagram'),
        ('web',        'Web'),
        ('walk_in',    'Walk-In'),
        ('referral',   'Referral'),
        ('whatsapp',   'WhatsApp'),
        ('other',      'Other'),
    )

    # 'winning' was merged into 'converted' (= Won) — see migration 0004.
    STAGE_CHOICES = (
        ('new_inquiries', 'New'),
        ('engaged',       'Contacted'),
        ('consultation',  'Consultation'),
        ('converted',     'Won'),
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
    next_action_date = models.DateField(null=True, blank=True)  # next follow-up date shown on the card
    # Set when the lead is converted (POST /convert/): the patient it became
    converted_patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='converted_from_leads')
    converted_at   = models.DateTimeField(null=True, blank=True)
    converted_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='leads_converted')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.stage}"


class LeadActivity(models.Model):
    objects = TenantManager.via('lead__clinic_id')()   # scoped to the current clinic via its parent

    ACTION_CHOICES = (
        ('call',           'Call'),
        ('whatsapp',       'WhatsApp'),
        ('email',          'Email'),
        ('meeting',        'Meeting'),
        ('note',           'Note'),
        ('stage_change',   'Stage Change'),
        ('created',        'Lead created'),
        ('assigned',       'Assignment changed'),
        ('converted',      'Converted to patient'),
        ('task_created',   'Task created'),
        ('task_completed', 'Task completed'),
        ('task_reopened',  'Task reopened'),
    )

    lead       = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    note       = models.TextField(blank=True)
    data       = models.JSONField(default=dict, blank=True)   # structured detail, e.g. {"from_stage_id": 3, "to_stage_id": 6}
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lead.name} — {self.action}"


class LeadTask(models.Model):
    """A follow-up to do for a lead (call back, send quote…), with a due date and done / not done."""
    objects = TenantManager.via('lead__clinic_id')()   # scoped to the current clinic via its parent

    lead        = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='tasks')
    title       = models.CharField(max_length=200)
    due_date    = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lead_tasks')
    is_done     = models.BooleanField(default=False)
    done_at     = models.DateTimeField(null=True, blank=True)
    done_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['is_done', 'due_date', 'id']
