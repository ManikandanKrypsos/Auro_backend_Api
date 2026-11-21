"""
Creating notifications. Call notify(...) after the change it describes has been saved.
It never raises: a notification problem must not break the action that caused it.
"""
import logging

log = logging.getLogger('aura.notifications')

# type → (label, description, roles that can receive it)
TYPES = {
    'leave_requested':        ('Leave requested',        'A staff member asked for time off',                   ('admin',)),
    'leave_approved':         ('Leave approved',         'Your leave was approved (or added for you)',          ('therapist', 'reception')),
    'leave_rejected':         ('Leave rejected',         'Your leave request was rejected',                    ('therapist', 'reception')),
    'appointment_booked':     ('New appointment',        'Someone booked an appointment with you',              ('therapist',)),
    'appointment_rescheduled': ('Appointment rescheduled', 'One of your appointments moved to a new time',      ('therapist',)),
    'appointment_cancelled':  ('Appointment cancelled',  'One of your appointments was cancelled',             ('therapist',)),
    'lead_assigned':          ('Lead assigned',          'A lead was assigned to you',                          ('admin', 'reception')),
}


def name_of(user):
    if user is None:
        return 'Someone'
    return user.username or (user.email.split('@')[0] if user.email else 'Someone')


def notify(recipients, type_, message, ref=None, actor=None):
    """Creates one notification per recipient — skipping the actor, inactive users,
    roles the type isn't for, and users who switched the type off."""
    try:
        from .models import Notification, NotificationPreference
        roles = TYPES[type_][2]
        people = {}
        for u in recipients or []:
            if u is None or not u.is_active or u.role not in roles:
                continue
            if actor is not None and u.pk == actor.pk:
                continue
            people[u.pk] = u
        if not people:
            return 0
        off = set(NotificationPreference.objects.filter(user_id__in=people, type=type_, enabled=False)
                  .values_list('user_id', flat=True))
        rows = [Notification(clinic_id=u.clinic_id, recipient=u, actor=actor, type=type_,
                             message=message[:300], ref=ref or {})
                for pk, u in people.items() if pk not in off]
        Notification.objects.bulk_create(rows)
        return len(rows)
    except Exception:
        log.exception('Could not create %s notification', type_)
        return 0


def clinic_admins(clinic_id):
    from users.models import User
    return list(User.all_objects.filter(clinic_id=clinic_id, role='admin', is_active=True))


# ── Events ────────────────────────────────────────────────────────────────────

def _dates(leave):
    if leave.from_date == leave.to_date:
        return leave.from_date.strftime('%d %b %Y')
    return f"{leave.from_date.strftime('%d %b')} – {leave.to_date.strftime('%d %b %Y')}"


def leave_requested(leave, actor):
    notify(clinic_admins(leave.staff.clinic_id), 'leave_requested',
           f"{name_of(leave.staff)} requested leave for {_dates(leave)}.",
           {'leave_id': leave.id, 'staff_id': leave.staff_id}, actor)


def leave_reviewed(leave, actor, added=False):
    if leave.status == 'approved':
        msg = (f"{name_of(actor)} added leave for you: {_dates(leave)}." if added
               else f"Your leave for {_dates(leave)} was approved.")
        type_ = 'leave_approved'
    elif leave.status == 'rejected':
        msg = f"Your leave request for {_dates(leave)} was rejected."
        type_ = 'leave_rejected'
    else:
        return
    if leave.review_note:
        msg += f' Note: {leave.review_note}'
    notify([leave.staff], type_, msg, {'leave_id': leave.id, 'staff_id': leave.staff_id}, actor)


def _when(appt):
    from django.utils import timezone
    return timezone.localtime(appt.date_time).strftime('%d %b %Y, %H:%M') if appt.date_time else ''


def _appt_ref(appt):
    return {'appointment_id': appt.id, 'patient_id': appt.patient.patient_id if appt.patient else None}


def appointment_booked(appt, actor):
    patient = appt.patient.name if appt.patient else 'A patient'
    treatment = f" — {appt.treatment.name}" if appt.treatment else ''
    notify([appt.staff], 'appointment_booked',
           f"New appointment: {patient}{treatment} on {_when(appt)}.", _appt_ref(appt), actor)


def appointment_rescheduled(appt, actor):
    patient = appt.patient.name if appt.patient else 'A patient'
    notify([appt.staff], 'appointment_rescheduled',
           f"{patient}'s appointment moved to {_when(appt)}.", _appt_ref(appt), actor)


def appointment_cancelled(appt, actor):
    patient = appt.patient.name if appt.patient else 'A patient'
    notify([appt.staff], 'appointment_cancelled',
           f"{patient}'s appointment on {_when(appt)} was cancelled.", _appt_ref(appt), actor)


def appointment_changed(before, appt, actor):
    """before = (staff_id, date_time, status) captured before the update."""
    staff_before, when_before, status_before = before
    if appt.status == 'cancelled' and status_before != 'cancelled':
        appointment_cancelled(appt, actor)
    elif appt.staff_id != staff_before:
        appointment_booked(appt, actor)              # it is new to the therapist it moved to
    elif appt.date_time != when_before and appt.status in ('upcoming', 'in_session'):
        appointment_rescheduled(appt, actor)


def lead_assigned(lead, actor):
    notify([lead.assigned_to], 'lead_assigned', f"Lead assigned to you: {lead.name}.", {'lead_id': lead.id}, actor)
