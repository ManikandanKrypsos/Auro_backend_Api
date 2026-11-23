import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

log = logging.getLogger('aura.invoicing')


@receiver(post_save, sender='appointments.Appointment', dispatch_uid='invoice_for_appointment')
def appointment_saved(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    try:
        from .invoicing import appointment_saved as sync
        sync(instance, created)
    except Exception:
        # never block saving an appointment; the invoice is re-synced on its next save / view
        log.exception('Invoice sync failed for appointment %s', instance.pk)
