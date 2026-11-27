"""
Every clinic-owned row gets its clinic automatically on save: from the current request's
clinic, or from its parent row (stock movements and lots take the item's clinic).
"""
from django.apps import apps
from django.db.models.signals import pre_save

from .context import get_current_clinic_id

# model label → attribute of a parent object to copy the clinic from (or None)
TENANT_MODELS = {
    'users.User': None,
    'patients.Patient': None,
    'appointments.Appointment': 'patient',
    'treatments.Treatment': None,
    'rooms.Room': None,
    'rooms.Equipment': None,
    'leads.Lead': None,
    'packages.PatientPackage': 'patient',
    'clinic.ClinicHours': None,
    'clinic.PlannedClosure': None,
    'inventory.Supplier': None,
    'inventory.InventoryItem': None,
    'inventory.PurchaseOrder': 'supplier',
    'inventory.StockMovement': 'item',
    'inventory.Lot': 'item',
    'payments.Invoice': 'patient',
    'payments.Payment': 'invoice',
    'audit.AuditEvent': None,
}


def _assign_clinic(sender, instance, **kwargs):
    # Inside a clinic user's request, rows ALWAYS belong to that clinic — whatever the
    # client sent (serializers with fields='__all__' would otherwise accept a "clinic" value).
    clinic_id = get_current_clinic_id()
    if clinic_id:
        instance.clinic_id = clinic_id
        return
    # No request clinic (migrations, commands, Celery, webhooks): take it from the parent row.
    if getattr(instance, 'clinic_id', None):
        return
    parent_attr = TENANT_MODELS.get(sender._meta.label)
    if parent_attr:
        parent = getattr(instance, parent_attr, None)
        if parent is not None and getattr(parent, 'clinic_id', None):
            instance.clinic_id = parent.clinic_id


for label in TENANT_MODELS:
    pre_save.connect(_assign_clinic, sender=apps.get_model(label), dispatch_uid=f'tenant-clinic-{label}')
