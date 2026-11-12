"""
GET /api/schedule/day/?date=2026-11-06[&grid_start=08:00&grid_end=21:00]

One day, every therapist and every room, for the calendar booking grid.
blocked_ranges types:
  closed  — outside clinic / staff hours, clinic closed, staff on leave or not scheduled
  break   — staff break
  booked  — an existing (non-cancelled) appointment
Room bookings include every therapist's appointments in that room.
"""
import datetime
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.models import User, StaffWorkingHours, StaffBreakTime, StaffLeave
from clinic.models import ClinicHours, PlannedClosure
from rooms.models import Room
from .models import Appointment
from .conflicts import DAY_CODES, _staff_name

DEFAULT_GRID = (datetime.time(8, 0), datetime.time(21, 0))


def _hm(t):
    return t.strftime('%H:%M')


def _parse_hm(value):
    try:
        return datetime.datetime.strptime(value.strip(), '%H:%M').time()
    except (ValueError, AttributeError):
        return None


def _outside(window_start, window_end, grid_start, grid_end, label):
    """'closed' ranges for the parts of the grid outside [window_start, window_end)."""
    out = []
    if grid_start < window_start:
        out.append({'start': _hm(grid_start), 'end': _hm(min(window_start, grid_end)), 'type': 'closed', 'label': label})
    if window_end < grid_end:
        out.append({'start': _hm(max(window_end, grid_start)), 'end': _hm(grid_end), 'type': 'closed', 'label': label})
    return out


class DayScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day = parse_date(request.query_params.get('date', '') or '')
        if not day:
            return Response({'error': 'date is required (YYYY-MM-DD).'}, status=400)
        code = DAY_CODES[day.weekday()]

        # ── Clinic ────────────────────────────────────────────────────────────
        closure = PlannedClosure.objects.filter(from_date__lte=day, to_date__gte=day).first()
        clinic  = ClinicHours.objects.filter(day=code).first()
        clinic_closed = bool(closure) or (clinic is not None and not clinic.is_open)
        clinic_window = None
        if clinic and clinic.is_open and clinic.open_time and clinic.close_time:
            clinic_window = (clinic.open_time, clinic.close_time)
        closed_label = (
            f"Clinic closed{' — ' + closure.reason if closure and closure.reason else ''}"
            if clinic_closed else None
        )

        # ── Staff data (one query each) ───────────────────────────────────────
        therapists = list(User.objects.filter(role='therapist', is_active=True).order_by('username', 'id'))
        ids   = [t.id for t in therapists]
        hours = {h.staff_id: h for h in StaffWorkingHours.objects.filter(staff_id__in=ids, day=code)}
        on_leave = set(StaffLeave.objects.filter(staff_id__in=ids, from_date__lte=day, to_date__gte=day)
                       .values_list('staff_id', flat=True))
        breaks = {}
        for b in StaffBreakTime.objects.filter(staff_id__in=ids).order_by('start_time'):
            breaks.setdefault(b.staff_id, []).append(b)

        # ── Grid (visible hours) ──────────────────────────────────────────────
        grid_start = _parse_hm(request.query_params.get('grid_start', ''))
        grid_end   = _parse_hm(request.query_params.get('grid_end', ''))
        if not grid_start or not grid_end or grid_start >= grid_end:
            starts = [h.start_time for h in hours.values()] + ([clinic_window[0]] if clinic_window else [])
            ends   = [h.end_time for h in hours.values()] + ([clinic_window[1]] if clinic_window else [])
            grid_start = min(starts) if starts else DEFAULT_GRID[0]
            grid_end   = max(ends) if ends else DEFAULT_GRID[1]

        # ── Appointments for the day (not cancelled) ──────────────────────────
        day_start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
        appts = list(
            Appointment.objects
            .filter(date_time__gte=day_start, date_time__lt=day_start + datetime.timedelta(days=1))
            .exclude(status='cancelled')
            .select_related('patient', 'staff', 'treatment', 'room_fk')
            .order_by('date_time')
        )

        def times(a):
            s = timezone.localtime(a.date_time)
            e = s + datetime.timedelta(minutes=a.duration or 0)
            return _hm(s), ('24:00' if e.date() != s.date() else _hm(e))

        by_staff, by_room = {}, {}
        for a in appts:
            by_staff.setdefault(a.staff_id, []).append(a)
            if a.room_fk_id:
                by_room.setdefault(a.room_fk_id, []).append(a)

        # ── Staff columns ─────────────────────────────────────────────────────
        staff_out = []
        for t in therapists:
            h = hours.get(t.id)
            reason = None
            if clinic_closed:
                reason, label = 'clinic_closed', closed_label
            elif t.id in on_leave:
                reason, label = 'staff_on_leave', 'On leave'
            elif not h:
                reason, label = 'not_scheduled', 'Not working today'

            blocked, window = [], None
            if reason:
                blocked.append({'start': _hm(grid_start), 'end': _hm(grid_end), 'type': 'closed', 'label': label})
            else:
                w_start, w_end = h.start_time, h.end_time
                if clinic_window:
                    w_start, w_end = max(w_start, clinic_window[0]), min(w_end, clinic_window[1])
                window = {'start': _hm(w_start), 'end': _hm(w_end)}
                if clinic_window and (clinic_window[0] > grid_start or clinic_window[1] < grid_end):
                    blocked += _outside(clinic_window[0], clinic_window[1], grid_start, grid_end, 'Outside clinic hours')
                    # staff-specific hours inside the clinic window
                    blocked += [r for r in _outside(w_start, w_end, clinic_window[0], clinic_window[1], 'Outside working hours')]
                else:
                    blocked += _outside(w_start, w_end, grid_start, grid_end, 'Outside working hours')
                for b in breaks.get(t.id, []):
                    blocked.append({'start': _hm(b.start_time), 'end': _hm(b.end_time),
                                    'type': 'break', 'label': b.label or 'Break'})

            appt_list = []
            for a in by_staff.get(t.id, []):
                s, e = times(a)
                blocked.append({'start': s, 'end': e, 'type': 'booked',
                                'label': f"{a.patient.name if a.patient else 'Patient'} — {a.treatment.name if a.treatment else 'Appointment'}",
                                'appointment_id': a.id})
                appt_list.append({
                    'appointment_id':  a.id,
                    'start':           s,
                    'end':             e,
                    'patient_id':      a.patient.patient_id if a.patient else None,
                    'patient_name':    a.patient.name if a.patient else None,
                    'treatment_id':    a.treatment_id,
                    'treatment':       a.treatment.name if a.treatment else None,
                    'room_id':         a.room_fk_id,
                    'room_name':       a.room_fk.name if a.room_fk else None,
                    'status':          a.status,
                    'patient_arrived': a.patient_arrived,
                })
            blocked.sort(key=lambda r: (r['start'], r['end']))
            staff_out.append({
                'staff_id':           t.id,
                'name':               _staff_name(t),
                'role':               t.specialist_area or 'Therapist',
                'profile_image':      t.profile_image or None,
                'is_available':       reason is None,
                'unavailable_reason': reason,
                'effective_window':   window,
                'blocked_ranges':     blocked,
                'appointments':       appt_list,
            })

        # ── Room columns ──────────────────────────────────────────────────────
        rooms_out = []
        for r in Room.objects.all().order_by('name'):
            blocked = []
            if clinic_closed:
                blocked.append({'start': _hm(grid_start), 'end': _hm(grid_end), 'type': 'closed', 'label': closed_label})
            elif clinic_window:
                blocked += _outside(clinic_window[0], clinic_window[1], grid_start, grid_end, 'Clinic closed')
            appt_list = []
            for a in by_room.get(r.id, []):
                s, e = times(a)
                staff_name = _staff_name(a.staff)
                blocked.append({'start': s, 'end': e, 'type': 'booked',
                                'label': f"{staff_name} — {a.treatment.name if a.treatment else 'Appointment'}",
                                'appointment_id': a.id, 'staff_id': a.staff_id, 'staff_name': staff_name})
                appt_list.append({
                    'appointment_id': a.id,
                    'start':          s,
                    'end':            e,
                    'staff_id':       a.staff_id,
                    'staff_name':     staff_name,
                    'patient_name':   a.patient.name if a.patient else None,
                    'treatment':      a.treatment.name if a.treatment else None,
                    'status':         a.status,
                })
            blocked.sort(key=lambda x: (x['start'], x['end']))
            rooms_out.append({
                'room_id':        r.id,
                'name':           r.name,
                'room_type':      r.room_type,
                'is_available':   not clinic_closed,
                'effective_window': (
                    None if clinic_closed else
                    {'start': _hm(clinic_window[0]), 'end': _hm(clinic_window[1])} if clinic_window else
                    {'start': _hm(grid_start), 'end': _hm(grid_end)}
                ),
                'blocked_ranges': blocked,
                'appointments':   appt_list,
            })

        return Response({
            'date':          str(day),
            'clinic': {
                'is_open':      not clinic_closed,
                'open':         _hm(clinic_window[0]) if clinic_window and not clinic_closed else None,
                'close':        _hm(clinic_window[1]) if clinic_window and not clinic_closed else None,
                'closed_reason': (closure.reason or 'Planned closure') if closure else ('Closed' if clinic_closed else None),
            },
            'grid':          {'start': _hm(grid_start), 'end': _hm(grid_end)},
            'staff':         staff_out,
            'rooms':         rooms_out,
        })
