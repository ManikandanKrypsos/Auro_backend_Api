import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

log = logging.getLogger('aura.courses')


@receiver(post_save, sender='appointments.Appointment', dispatch_uid='course_plan_link')
def appointment_booked(sender, instance, created, raw=False, **kwargs):
    if raw or not created:
        return
    try:
        from .course_views import link_booked_appointment
        link_booked_appointment(instance)
    except Exception:
        log.exception('Could not link appointment %s to a planned session', instance.pk)
