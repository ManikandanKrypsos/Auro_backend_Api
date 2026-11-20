"""
Shared booking-conflict checks used by appointment create / update.
Returns a structured dict (sent back as HTTP 409) or None when the slot is free.
"""
import datetime
from django.utils import timezone

from users.models import StaffWorkingHours, StaffBreakTime, StaffLeave
from clinic.models import ClinicHours, PlannedClosure
from .models import Appointment

ACTIVE_STATUSES = ('upcoming', 'in_session')
DAY_CODES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _hm(t):
    return t.strftime('%H:%M')


def _staff_name(user):
    if not user:
        return None
    return user.username or user.email.split('@')[0]


def _first_overlap(qs, start, end, exclude_id=None):
    """First active appointment in qs overlapping [start, end) — any staff member."""
    qs = qs.filter(
        status__in=ACTIVE_STATUSES,
        date_time__lt=end,
        date_time__gt=start - datetime.timedelta(hours=24),
    ).select_related('staff', 'room_fk', 'treatment').order_by('date_time')
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    for a in qs:
        a_end = a.date_time + datetime.timedelta(minutes=a.duration or 0)
        if start < a_end and end > a.date_time:
            return a, a_end
    return None, None


def find_conflict(start, duration, staff=None, room=None, exclude_id=None):
    """
    start      — timezone-aware datetime
    duration   — minutes
    staff/room — User / Room instances (optional)
    exclude_id — appointment being edited (ignored when checking overlaps)

    Checks, in order: clinic_closed, outside_clinic_hours, staff_on_leave,
    staff_not_working, outside_staff_hours, staff_break, staff_double_booked,
    room_double_booked. Room checks include every staff member's bookings.
    """
    end         = start + datetime.timedelta(minutes=duration)
    local_start = timezone.localtime(start)
    local_end   = timezone.localtime(end)
    day         = local_start.date()
    code        = DAY_CODES[day.weekday()]
    st, et      = local_start.time(), local_end.time()
    crosses_day = local_end.date() != day and local_end.time() != datetime.time(0, 0)
    if local_end.date() != day and local_end.time() == datetime.time(0, 0):
        et = datetime.time(23, 59, 59)

    def conflict(ctype, message, **extra):
        out = {
            'error':                      'conflict',
            'conflict_type':              ctype,
            'message':                    message,
            'conflicting_appointment_id': None,
            'staff_name':                 _staff_name(staff),
            'room_name':                  room.name if room else None,
            'treatment':                  None,
            'blocked_until':              None,
        }
        out.update(extra)
        return out

    # ── Clinic ────────────────────────────────────────────────────────────────
    closure = PlannedClosure.objects.filter(from_date__lte=day, to_date__gte=day).first()
    clinic  = ClinicHours.objects.filter(day=code).first()
    if closure:
        return conflict('clinic_closed',
                        f"The clinic is closed from {closure.from_date} to {closure.to_date}"
                        + (f" ({closure.reason})." if closure.reason else "."),
                        blocked_until=str(closure.to_date))
    if clinic and not clinic.is_open:
        return conflict('clinic_closed', f"The clinic is closed on {code}.")
    if clinic and clinic.open_time and clinic.close_time:
        if st < clinic.open_time or et > clinic.close_time or crosses_day:
            return conflict('outside_clinic_hours',
                            f"Clinic hours on {code} are {_hm(clinic.open_time)}–{_hm(clinic.close_time)}; "
                            f"this booking runs {_hm(st)}–{_hm(local_end.time())}.",
                            blocked_until=_hm(clinic.open_time) if st < clinic.open_time else None)

    # ── Staff ─────────────────────────────────────────────────────────────────
    if staff:
        name  = _staff_name(staff)
        leave = StaffLeave.objects.filter(staff=staff, status='approved', from_date__lte=day, to_date__gte=day).first()
        if leave:
            return conflict('staff_on_leave',
                            f"{name} is on leave from {leave.from_date} to {leave.to_date}.",
                            blocked_until=str(leave.to_date))

        hours = StaffWorkingHours.objects.filter(staff=staff, day=code).first()
        if not hours:
            return conflict('staff_not_working', f"{name} does not work on {code}.")
        if st < hours.start_time or et > hours.end_time or crosses_day:
            return conflict('outside_staff_hours',
                            f"{name} works {_hm(hours.start_time)}–{_hm(hours.end_time)} on {code}; "
                            f"this booking runs {_hm(st)}–{_hm(local_end.time())}.",
                            blocked_until=_hm(hours.start_time) if st < hours.start_time else None)

        for br in StaffBreakTime.objects.filter(staff=staff):
            if st < br.end_time and et > br.start_time:
                return conflict('staff_break',
                                f"Overlaps {name}'s {br.label or 'break'} "
                                f"({_hm(br.start_time)}–{_hm(br.end_time)}).",
                                blocked_until=_hm(br.end_time))

        a, a_end = _first_overlap(Appointment.objects.filter(staff=staff), start, end, exclude_id)
        if a:
            return conflict('staff_double_booked',
                            f"{name} already has {a.treatment.name if a.treatment else 'an appointment'} "
                            f"{_hm(timezone.localtime(a.date_time))}–{_hm(timezone.localtime(a_end))}.",
                            conflicting_appointment_id=a.id,
                            room_name=a.room_fk.name if a.room_fk else (room.name if room else None),
                            treatment=a.treatment.name if a.treatment else None,
                            blocked_until=_hm(timezone.localtime(a_end)))

    # ── Room (any therapist's booking) ────────────────────────────────────────
    if room:
        a, a_end = _first_overlap(Appointment.objects.filter(room_fk=room), start, end, exclude_id)
        if a:
            return conflict('room_double_booked',
                            f"{room.name} is booked by {_staff_name(a.staff) or 'another therapist'} for "
                            f"{a.treatment.name if a.treatment else 'an appointment'} "
                            f"{_hm(timezone.localtime(a.date_time))}–{_hm(timezone.localtime(a_end))}.",
                            conflicting_appointment_id=a.id,
                            staff_name=_staff_name(a.staff),
                            treatment=a.treatment.name if a.treatment else None,
                            blocked_until=_hm(timezone.localtime(a_end)))
    return None


def own_schedule_only(request, staff_id):
    """
    Therapists may only look at their own schedule. Returns a 403 Response when a therapist asks
    for someone else's staff_id, else None. Admin / reception: no restriction.
    """
    from rest_framework.response import Response
    if getattr(request.user, 'role', '') != 'therapist' or staff_id in (None, ''):
        return None
    if str(staff_id).strip() != str(request.user.pk):
        return Response({'error': 'Therapists can only view their own schedule.', 'code': 'not_own_schedule'}, status=403)
    return None
