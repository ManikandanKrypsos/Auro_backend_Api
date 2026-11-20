"""Therapists may only see patients they have (or had) appointments with, or that they added themselves."""


def can_access_patient(user, patient):
    if getattr(user, 'role', '') != 'therapist':
        return True
    if patient.created_by_id == user.pk:
        return True
    from appointments.models import Appointment
    return Appointment.objects.filter(staff_id=user.pk, patient=patient).exists()
