import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

log = logging.getLogger('aura.consumption')


@receiver(post_save, sender='appointments.Appointment', dispatch_uid='treatment_consumption')
def appointment_saved(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    try:
        from .consumption import appointment_saved as sync
        sync(instance)
    except Exception:
        # never block completing an appointment because of stock bookkeeping
        log.exception('Consumable deduction failed for appointment %s', instance.pk)
