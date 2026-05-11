from rest_framework import serializers
from .models import PatientPackage

STATUS_MAP      = {1: 'active', 2: 'completed', 3: 'cancelled'}
PAY_TYPE_MAP    = {1: 'online', 2: 'cash'}
PAY_STATUS_MAP  = {1: 'pending', 2: 'paid', 3: 'refunded'}


def _patient_detail(p):
    if not p:
        return None
    from django.utils import timezone
    import datetime
    age = None
    if p.dob:
        today = datetime.date.today()
        age = today.year - p.dob.year - ((today.month, today.day) < (p.dob.month, p.dob.day))
    return {
        'id':         p.id,
        'patient_id': p.patient_id,
        'name':       p.name,
        'phone':      p.phone,
        'email':      p.email,
        'gender':     p.gender,
        'age':        age,
        'image':      p.image or None,
    }


def _treatment_detail(t, plan=None):
    if not t:
        return None
    return {
        'id':       t.id,
        'name':     t.name,
        'duration': t.duration,
        'category': t.category,
        'price':    str(plan.price) if plan else None,
        'sessions': plan.sessions if plan else None,
    }


def _plan_detail(plan):
    if not plan:
        return None
    return {
        'id':       plan.id,
        'sessions': plan.sessions,
        'price':    str(plan.price),
    }


def _package_summary(pkg):
    return {
        'id':                  pkg.id,
        'total_sessions':      pkg.total_sessions,
        'sessions_completed':  pkg.sessions_completed,
        'sessions_remaining':  pkg.sessions_remaining,
        'status':              pkg.status,
        'status_id':           pkg.status_id,
        'updated_at':          pkg.updated_at,
    }


def _package_full(pkg, include_sessions=False):
    data = {
        'id':                  pkg.id,
        'patient_detail':      _patient_detail(pkg.patient),
        'treatment_detail':    _treatment_detail(pkg.treatment, pkg.price_plan),
        'price_plan_detail':   _plan_detail(pkg.price_plan),
        'total_sessions':      pkg.total_sessions,
        'sessions_completed':  pkg.sessions_completed,
        'sessions_remaining':  pkg.sessions_remaining,
        'status':              pkg.status,
        'status_id':           pkg.status_id,
        'payment_amount':      str(pkg.payment_amount),
        'payment_type':        pkg.payment_type,
        'payment_type_id':     pkg.payment_type_id,
        'payment_status':      pkg.payment_status,
        'payment_status_id':   pkg.payment_status_id,
        'notes':               pkg.notes,
        'created_at':          pkg.created_at,
        'updated_at':          pkg.updated_at,
    }
    if include_sessions:
        data['sessions'] = _build_sessions(pkg)
    return data


def _build_sessions(pkg):
    """Build exactly total_sessions items — scheduled + unscheduled."""
    from appointments.models import Appointment
    from django.utils import timezone as tz

    appts = list(
        Appointment.objects.filter(package=pkg)
        .select_related('staff', 'room_fk')
        .order_by('session_number')
    )
    appt_map = {a.session_number: a for a in appts}

    STATUS_ID = {'upcoming': 1, 'completed': 3, 'cancelled': 4, 'no_show': 5}

    sessions = []
    for i in range(1, pkg.total_sessions + 1):
        a = appt_map.get(i)
        if a:
            dt = tz.localtime(a.date_time) if a.date_time and tz.is_aware(a.date_time) else a.date_time
            sessions.append({
                'appointment_id': a.id,
                'session_number': i,
                'status':         a.status,
                'status_id':      STATUS_ID.get(a.status, 1),
                'date':           str(dt.date()) if dt else None,
                'time':           dt.strftime('%H:%M') if dt else None,
                'staff_detail':   {
                    'id':            a.staff.id,
                    'name':          a.staff.username or a.staff.email.split('@')[0],
                    'role':          a.staff.role,
                    'profile_image': a.staff.profile_image or None,
                } if a.staff else None,
                'room_detail': {
                    'id':        a.room_fk.id,
                    'name':      a.room_fk.name,
                    'room_type': a.room_fk.room_type,
                } if a.room_fk else None,
            })
        else:
            sessions.append({
                'appointment_id': None,
                'session_number': i,
                'status':         'unscheduled',
                'status_id':      0,
                'date':           None,
                'time':           None,
                'staff_detail':   None,
                'room_detail':    None,
            })
    return sessions