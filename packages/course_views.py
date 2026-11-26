"""
Treatment courses — the patient's Protocol tab: goal + progress, pre-planned sessions, and the
patient's own copy of the treatment protocol.

GET    /api/courses/?patient_id=Aura12&status=active      list (opt-in ?page=&page_size=)
POST   /api/courses/                                      {patient_id, package_id | treatment_id, goal?, target_date?}
GET    /api/courses/<id>/
PATCH  /api/courses/<id>/                                 goal, target_date, status, protocol fields
DELETE /api/courses/<id>/                                 admin / reception
POST   /api/courses/<id>/reset-protocol/                  copy the protocol from the service again
POST   /api/courses/<id>/progress/                        {date?, progress_pct?, note?, appointment_id?}
PATCH  /api/courses/<id>/progress/<entry_id>/   DELETE
POST   /api/courses/<id>/plan/                            {planned_date, planned_time?, staff_id?, notes?, session_number?, appointment_id?}
PATCH  /api/courses/<id>/plan/<planned_id>/     DELETE
POST   /api/courses/<id>/plan/generate/                   {start_date, count?, every_value?, every_unit?, planned_time?, staff_id?}

Who: any clinic staff. Therapists only for patients they can see (treated or added by them).
"""
import calendar
import datetime

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsClinicStaff
from utils.api_errors import error, validation_error
from .models import CourseProgress, PatientPackage, PlannedSession, TreatmentCourse

UNITS = dict(TreatmentCourse._meta.get_field('recommended_frequency_unit').choices)
STATUSES = dict(TreatmentCourse.STATUS_CHOICES)


def _name(u):
    return (u.username or u.email.split('@')[0]) if u else None


def _patient(value):
    from patients.models import Patient
    v = str(value or '').strip()
    if not v:
        return None
    p = Patient.objects.filter(patient_id__iexact=v).first()
    if p is None and v.isdigit():
        p = Patient.objects.filter(pk=int(v)).first()
    return p


def _can_see(user, patient):
    from patients.access import can_access_patient
    return can_access_patient(user, patient)


def _course(request, pk):
    c = (TreatmentCourse.objects.select_related('patient', 'treatment', 'package', 'created_by')
         .filter(pk=pk).first())
    if c is None or not _can_see(request.user, c.patient):
        return None
    return c


def _date(v, field, errors, required=False):
    if v in (None, ''):
        if required:
            errors[field] = 'This field is required (YYYY-MM-DD).'
        return None
    d = parse_date(str(v))
    if not d:
        errors[field] = 'Use YYYY-MM-DD.'
    return d


def _appointment(course, value, errors, field='appointment_id'):
    from appointments.models import Appointment
    if value in (None, ''):
        return None
    a = Appointment.objects.filter(pk=int(value)).first() if str(value).isdigit() else None
    if a is None or a.patient_id != course.patient_id:
        errors[field] = "Appointment not found for this patient."
        return None
    return a


def _staff(value, errors):
    from users.models import User
    if value in (None, ''):
        return None
    s = User.objects.filter(pk=int(value), role__in=['therapist', 'reception', 'admin']).first() \
        if str(value).isdigit() else None
    if s is None:
        errors['staff_id'] = 'Staff member not found.'
    return s


# ── read ─────────────────────────────────────────────────────────────────────

def course_appointments(course):
    from appointments.models import Appointment
    qs = Appointment.objects.filter(patient_id=course.patient_id)
    if course.package_id:
        qs = qs.filter(package_id=course.package_id)
    else:
        qs = qs.filter(treatment_id=course.treatment_id, package__isnull=True)
    return qs.order_by('date_time')


def _plan_state(p, today):
    if p.appointment_id and p.appointment:
        return {'upcoming': 'booked'}.get(p.appointment.status, p.appointment.status)
    return 'overdue' if p.planned_date < today else 'planned'


def serialize(course):
    today = timezone.localdate()
    appts = list(course_appointments(course).select_related('staff'))
    completed = [a for a in appts if a.status == 'completed']
    now = timezone.now()
    nxt = next((a for a in appts if a.status in ('upcoming', 'in_session') and a.date_time >= now - datetime.timedelta(hours=12)), None)
    plan = list(course.planned_sessions.select_related('staff', 'appointment'))
    total = course.package.total_sessions if course.package_id else (max([p.session_number for p in plan], default=0) or None)
    entries = list(course.progress_entries.select_related('created_by', 'appointment'))
    latest_pct = next((e.progress_pct for e in entries if e.progress_pct is not None), None)
    t = course.treatment
    customized = any(
        (getattr(course, f) or (None if f.endswith('_value') else ('' if f != 'contraindications' else [])))
        != (getattr(t, f) or (None if f.endswith('_value') else ('' if f != 'contraindications' else [])))
        for f in TreatmentCourse.PROTOCOL_FIELDS)
    pkg = course.package
    return {
        'id': course.id,
        'patient_id': course.patient.patient_id, 'patient_name': course.patient.name,
        'treatment': {'id': t.id, 'name': t.name},
        'package': {'id': pkg.id, 'total_sessions': pkg.total_sessions, 'sessions_completed': pkg.sessions_completed,
                    'status': pkg.status} if pkg else None,
        'status': course.status, 'status_label': STATUSES.get(course.status, course.status),
        'goal': course.goal, 'target_date': str(course.target_date) if course.target_date else None,
        'progress_pct': latest_pct,
        'progress': [{
            'id': e.id, 'date': str(e.date), 'progress_pct': e.progress_pct, 'note': e.note,
            'appointment_id': e.appointment_id, 'by': _name(e.created_by), 'created_at': e.created_at.isoformat(),
        } for e in entries],
        'sessions': {
            'total': total, 'completed': len(completed),
            'remaining': max(total - len(completed), 0) if total else None,
            'next_appointment': {'id': nxt.id, 'date_time': nxt.date_time.isoformat(), 'status': nxt.status,
                                 'session_number': nxt.session_number} if nxt else None,
        },
        'plan': [{
            'id': p.id, 'session_number': p.session_number, 'planned_date': str(p.planned_date),
            'planned_time': p.planned_time.strftime('%H:%M') if p.planned_time else None,
            'staff_id': p.staff_id, 'staff_name': _name(p.staff), 'notes': p.notes,
            'appointment_id': p.appointment_id,
            'appointment_date_time': p.appointment.date_time.isoformat() if p.appointment_id and p.appointment else None,
            'state': _plan_state(p, today),     # planned | overdue | booked | in_session | completed | cancelled | no_show
        } for p in plan],
        'protocol': {
            'pre_care_instructions': course.pre_care_instructions,
            'post_care_instructions': course.post_care_instructions,
            'contraindications': course.contraindications or [],
            'recommended_frequency_value': course.recommended_frequency_value,
            'recommended_frequency_unit': course.recommended_frequency_unit or None,
            'notes': course.protocol_notes,
            'customized': customized,           # differs from the service's protocol
        },
        'appointments': [{'id': a.id, 'date_time': a.date_time.isoformat(), 'status': a.status,
                          'session_number': a.session_number, 'staff_name': _name(a.staff)} for a in appts],
        'created_by': _name(course.created_by), 'created_at': course.created_at.isoformat(),
        'updated_at': course.updated_at.isoformat(),
    }


# ── courses ──────────────────────────────────────────────────────────────────

def _apply_course_fields(course, data, errors):
    if 'goal' in data:
        course.goal = str(data.get('goal') or '')
    if 'target_date' in data:
        course.target_date = _date(data.get('target_date'), 'target_date', errors)
    if 'status' in data:
        if data['status'] not in STATUSES:
            errors['status'] = f'Use one of: {", ".join(STATUSES)}.'
        else:
            course.status = data['status']
    for f in ('pre_care_instructions', 'post_care_instructions'):
        if f in data:
            setattr(course, f, str(data.get(f) or ''))
    if 'protocol_notes' in data:
        course.protocol_notes = str(data.get('protocol_notes') or '')
    if 'contraindications' in data:
        v = data.get('contraindications') or []
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            errors['contraindications'] = 'A list of text items.'
        else:
            course.contraindications = [x.strip() for x in v if x.strip()]
    if 'recommended_frequency_value' in data:
        v = data.get('recommended_frequency_value')
        if v in (None, ''):
            course.recommended_frequency_value = None
        elif not str(v).isdigit() or int(v) < 1:
            errors['recommended_frequency_value'] = 'A whole number of 1 or more (or null).'
        else:
            course.recommended_frequency_value = int(v)
    if 'recommended_frequency_unit' in data:
        v = data.get('recommended_frequency_unit') or ''
        if v and v not in UNITS:
            errors['recommended_frequency_unit'] = 'Use days, weeks or months (or null).'
        else:
            course.recommended_frequency_unit = v


class CourseListView(APIView):
    permission_classes = [IsClinicStaff]

    def get(self, request):
        from utils.pagination import paginate
        p = request.query_params
        qs = TreatmentCourse.objects.select_related('patient', 'treatment', 'package', 'created_by')
        if p.get('patient_id'):
            patient = _patient(p['patient_id'])
            if not patient or not _can_see(request.user, patient):
                return error(404, 'patient_not_found', 'Patient not found.')
            qs = qs.filter(patient=patient)
        elif getattr(request.user, 'role', '') == 'therapist':
            qs = qs.filter(Q(patient__appointments__staff=request.user) | Q(patient__created_by=request.user)).distinct()
        if p.get('status'):
            qs = qs.filter(status__in=[s.strip() for s in p['status'].split(',') if s.strip()])
        if p.get('treatment_id') and str(p['treatment_id']).isdigit():
            qs = qs.filter(treatment_id=int(p['treatment_id']))
        return paginate(request, qs, lambda objs: [serialize(c) for c in objs])

    def post(self, request):
        from treatments.models import Treatment
        d = request.data
        errors = {}
        patient = _patient(d.get('patient_id'))
        if not patient or not _can_see(request.user, patient):
            errors['patient_id'] = 'Patient not found.'
        package = treatment = None
        if d.get('package_id') not in (None, ''):
            package = PatientPackage.objects.select_related('treatment').filter(pk=int(d['package_id'])).first() \
                if str(d['package_id']).isdigit() else None
            if package is None or (patient and package.patient_id != patient.id):
                errors['package_id'] = "Package not found for this patient."
            else:
                treatment = package.treatment
        elif d.get('treatment_id') not in (None, ''):
            treatment = Treatment.objects.filter(pk=int(d['treatment_id'])).first() if str(d['treatment_id']).isdigit() else None
            if treatment is None:
                errors['treatment_id'] = 'Treatment not found.'
        else:
            errors['package_id'] = 'Send package_id, or treatment_id when the patient has no package.'
        if errors:
            return validation_error(errors)
        if package and TreatmentCourse.objects.filter(package=package).exists():
            return error(409, 'course_exists', 'This package already has a course.')
        if not package and TreatmentCourse.objects.filter(patient=patient, treatment=treatment, package__isnull=True,
                                                          status__in=('active', 'paused')).exists():
            return error(409, 'course_exists', f'{patient.name} already has an open {treatment.name} course.')
        course = TreatmentCourse(patient=patient, treatment=treatment, package=package, created_by=request.user)
        course.copy_protocol_from_treatment()
        _apply_course_fields(course, d, errors)
        if errors:
            return validation_error(errors)
        try:
            course.save()
        except IntegrityError:
            return error(409, 'course_exists', 'This package already has a course.')
        return Response(serialize(course), status=201)


class CourseDetailView(APIView):
    permission_classes = [IsClinicStaff]

    def get(self, request, pk):
        c = _course(request, pk)
        if not c:
            return error(404, 'course_not_found', 'Course not found.')
        return Response(serialize(c))

    def patch(self, request, pk):
        c = _course(request, pk)
        if not c:
            return error(404, 'course_not_found', 'Course not found.')
        errors = {}
        _apply_course_fields(c, request.data, errors)
        if errors:
            return validation_error(errors)
        c.save()
        return Response(serialize(c))

    def delete(self, request, pk):
        if getattr(request.user, 'role', '') not in ('admin', 'reception'):
            return error(403, 'not_permitted', 'Only admin or reception can delete a course.')
        c = _course(request, pk)
        if not c:
            return error(404, 'course_not_found', 'Course not found.')
        c.delete()
        return Response({'message': 'Course deleted.'})


class CourseResetProtocolView(APIView):
    permission_classes = [IsClinicStaff]

    def post(self, request, pk):
        c = _course(request, pk)
        if not c:
            return error(404, 'course_not_found', 'Course not found.')
        c.copy_protocol_from_treatment()
        c.save()
        return Response(serialize(c))


# ── progress ─────────────────────────────────────────────────────────────────

def _apply_progress(entry, course, data, errors, creating):
    if 'date' in data or creating:
        entry.date = _date(data.get('date'), 'date', errors) or (entry.date if not creating else timezone.localdate())
    if 'progress_pct' in data:
        v = data.get('progress_pct')
        if v in (None, ''):
            entry.progress_pct = None
        elif not str(v).isdigit() or int(v) > 100:
            errors['progress_pct'] = 'A whole number from 0 to 100 (or null).'
        else:
            entry.progress_pct = int(v)
    if 'note' in data:
        entry.note = str(data.get('note') or '')
    if 'appointment_id' in data:
        entry.appointment = _appointment(course, data.get('appointment_id'), errors)
    if not errors and entry.progress_pct is None and not entry.note.strip():
        errors['note'] = 'Send a note and/or a progress_pct.'


class CourseProgressView(APIView):
    permission_classes = [IsClinicStaff]

    def post(self, request, pk):
        c = _course(request, pk)
        if not c:
            return error(404, 'course_not_found', 'Course not found.')
        errors = {}
        e = CourseProgress(course=c, created_by=request.user, note='')
        _apply_progress(e, c, request.data, errors, creating=True)
        if errors:
            return validation_error(errors)
        e.save()
        return Response(serialize(c), status=201)


class CourseProgressDetailView(APIView):
    permission_classes = [IsClinicStaff]

    def _get(self, request, pk, entry_id):
        c = _course(request, pk)
        return (c, CourseProgress.objects.filter(pk=entry_id, course=c).first()) if c else (None, None)

    def patch(self, request, pk, entry_id):
        c, e = self._get(request, pk, entry_id)
        if not e:
            return error(404, 'progress_not_found', 'Progress entry not found.')
        errors = {}
        _apply_progress(e, c, request.data, errors, creating=False)
        if errors:
            return validation_error(errors)
        e.save()
        return Response(serialize(c))

    def delete(self, request, pk, entry_id):
        c, e = self._get(request, pk, entry_id)
        if not e:
            return error(404, 'progress_not_found', 'Progress entry not found.')
        e.delete()
        return Response(serialize(c))


# ── planned sessions ─────────────────────────────────────────────────────────

def _apply_plan(p, course, data, errors, creating):
    if 'planned_date' in data or creating:
        d = _date(data.get('planned_date'), 'planned_date', errors, required=creating or 'planned_date' in data)
        if d:
            p.planned_date = d
    if 'planned_time' in data:
        v = data.get('planned_time')
        t = parse_time(str(v)) if v not in (None, '') else None
        if v not in (None, '') and t is None:
            errors['planned_time'] = 'Use HH:MM.'
        p.planned_time = t
    if 'staff_id' in data:
        p.staff = _staff(data.get('staff_id'), errors)
    if 'notes' in data:
        p.notes = str(data.get('notes') or '')
    if 'session_number' in data and data.get('session_number') not in (None, ''):
        v = data['session_number']
        if not str(v).isdigit() or int(v) < 1:
            errors['session_number'] = 'A whole number of 1 or more.'
        else:
            p.session_number = int(v)
    if 'appointment_id' in data:
        p.appointment = _appointment(course, data.get('appointment_id'), errors)


def _next_number(course):
    done = course_appointments(course).filter(status='completed').count()
    planned = max(course.planned_sessions.values_list('session_number', flat=True), default=0)
    return max(done, planned) + 1


def _save_plan(p):
    try:
        with transaction.atomic():
            p.save()
    except IntegrityError:
        return error(409, 'plan_conflict', 'That session number is already planned, or the appointment is linked to another planned session.')
    return None


class CoursePlanView(APIView):
    permission_classes = [IsClinicStaff]

    def post(self, request, pk):
        c = _course(request, pk)
        if not c:
            return error(404, 'course_not_found', 'Course not found.')
        errors = {}
        p = PlannedSession(course=c, notes='')
        _apply_plan(p, c, request.data, errors, creating=True)
        if errors:
            return validation_error(errors)
        if not p.session_number:
            p.session_number = _next_number(c)
        bad = _save_plan(p)
        return bad or Response(serialize(c), status=201)


class CoursePlanDetailView(APIView):
    permission_classes = [IsClinicStaff]

    def _get(self, request, pk, plan_id):
        c = _course(request, pk)
        return (c, PlannedSession.objects.filter(pk=plan_id, course=c).first()) if c else (None, None)

    def patch(self, request, pk, plan_id):
        c, p = self._get(request, pk, plan_id)
        if not p:
            return error(404, 'planned_session_not_found', 'Planned session not found.')
        errors = {}
        _apply_plan(p, c, request.data, errors, creating=False)
        if errors:
            return validation_error(errors)
        bad = _save_plan(p)
        return bad or Response(serialize(c))

    def delete(self, request, pk, plan_id):
        c, p = self._get(request, pk, plan_id)
        if not p:
            return error(404, 'planned_session_not_found', 'Planned session not found.')
        p.delete()
        return Response(serialize(c))


def _add(d, value, unit):
    if unit == 'days':
        return d + datetime.timedelta(days=value)
    if unit == 'weeks':
        return d + datetime.timedelta(weeks=value)
    m = d.month - 1 + value
    y, m = d.year + m // 12, m % 12 + 1
    return datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


class CoursePlanGenerateView(APIView):
    """
    Fills the plan from start_date at the protocol's frequency (or every_value + every_unit).
    count: how many sessions (default: the package's sessions not yet completed or planned).
    Existing planned sessions are kept; numbering continues after them.
    """
    permission_classes = [IsClinicStaff]

    def post(self, request, pk):
        c = _course(request, pk)
        if not c:
            return error(404, 'course_not_found', 'Course not found.')
        d, errors = request.data, {}
        start = _date(d.get('start_date'), 'start_date', errors, required=True)
        every = d.get('every_value') or c.recommended_frequency_value
        unit = d.get('every_unit') or c.recommended_frequency_unit
        if not str(every or '').isdigit() or int(every) < 1:
            errors['every_value'] = "The protocol has no recommended frequency — send every_value (and every_unit)."
        if unit not in UNITS:
            errors['every_unit'] = 'Use days, weeks or months.'
        first = _next_number(c)
        count = d.get('count')
        if count in (None, ''):
            count = (c.package.total_sessions - first + 1) if c.package_id else None
            if count is None:
                errors['count'] = 'How many sessions to plan (required when there is no package).'
        elif not str(count).isdigit() or not 1 <= int(count) <= 52:
            errors['count'] = 'A whole number from 1 to 52.'
        t = None
        if d.get('planned_time') not in (None, ''):
            t = parse_time(str(d['planned_time']))
            if t is None:
                errors['planned_time'] = 'Use HH:MM.'
        staff = _staff(d.get('staff_id'), errors)
        if errors:
            return validation_error(errors)
        count = int(count)
        if count < 1:
            return error(400, 'nothing_to_plan', 'All sessions of this package are already completed or planned.')
        with transaction.atomic():
            for i in range(count):
                PlannedSession.objects.create(course=c, session_number=first + i, planned_date=_add(start, int(every) * i, unit),
                                              planned_time=t, staff=staff, notes='')
        return Response(serialize(c), status=201)


# ── booking → plan link ──────────────────────────────────────────────────────

def link_booked_appointment(appt):
    """A newly booked appointment fills the matching planned session (same date, else same session number)."""
    if not appt.patient_id or not appt.treatment_id:
        return
    if appt.package_id:
        course = TreatmentCourse.objects.filter(package_id=appt.package_id).first()
    else:
        course = TreatmentCourse.objects.filter(patient_id=appt.patient_id, treatment_id=appt.treatment_id,
                                                package__isnull=True, status__in=('active', 'paused')).first()
    if not course:
        return
    free = course.planned_sessions.filter(appointment__isnull=True)
    day = timezone.localtime(appt.date_time).date()
    p = free.filter(planned_date=day).first()
    if p is None and appt.package_id:
        p = free.filter(session_number=appt.session_number).first()
    if p:
        p.appointment = appt
        p.save(update_fields=['appointment', 'updated_at'])
