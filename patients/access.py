"""Therapists may only see patients they have (or had) appointments with."""


def can_access_patient(user, patient):
    if getattr(user, 'role', '') != 'therapist':
        return True
    from appointments.models import Appointment
    return Appointment.objects.filter(staff_id=user.pk, patient=patient).exists()
