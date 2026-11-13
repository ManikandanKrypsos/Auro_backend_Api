from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Sum, Q
import datetime
from appointments.models import Appointment
from patients.models import Patient
from treatments.models import Treatment
from leads.models import Lead
from users.models import User, StaffWorkingHours, StaffBreakTime, StaffLeave
from clinic.models import ClinicHours, PlannedClosure
from payments.metrics import paid_total, billable, in_dates, month_bounds


def _calc_trend(current, previous):
    """Calculate percentage change and trend direction."""
    if previous == 0:
        pct = 100.0 if current > 0 else 0.0
        trend = 'up' if current > 0 else 'neutral'
    else:
        pct = round(((current - previous) / previous) * 100, 1)
        trend = 'up' if pct > 0 else ('down' if pct < 0 else 'neutral')
    return {'value': current, 'change_pct': abs(pct), 'trend': trend}


def _get_greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return 'Good Morning'
    elif hour < 17:
        return 'Good Afternoon'
    return 'Good Evening'


def _fmt_appt(a):
    return {
        'id':              a.id,
        'time':            timezone.localtime(a.date_time).strftime('%I:%M %p') if a.date_time else None,
        'time_24':         timezone.localtime(a.date_time).strftime('%H:%M') if a.date_time else None,
        'patient_name':    a.patient.name if a.patient else None,
        'treatment':       a.treatment.name if a.treatment else None,
        'staff_name':      a.staff.username if a.staff else None,
        'duration':        a.duration,
        'room':            a.room_fk.name if a.room_fk else None,
        'status':          a.status,
        'patient_arrived': a.patient_arrived,
        'consent_status':  a.consent_status,
    }


# ── Shared helpers for chart / occupancy / tasks ─────────────────────────────

CHART_RANGES = ('week', 'month', 'year')
DEFAULT_CHART_RANGE = 'month'
DAY_CODES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']   # date.weekday() → code


def _revenue_total(qs):
    """Revenue = paid payment_amount (shared rule with /api/payments/, see payments/metrics.py)."""
    return paid_total(qs)


def _get_chart_range(request):
    value = (request.query_params.get('chart_range') or DEFAULT_CHART_RANGE).lower()
    return value if value in CHART_RANGES else DEFAULT_CHART_RANGE


def _day_start(day):
    """Timezone-aware datetime for 00:00 of a local date."""
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))


MAX_CHART_YEARS = 10


def _build_revenue_chart(chart_range, today):
    """
    week  → 7 points, Monday–Sunday of the current week (date = each day)
    month → 12 points, January–December of the current year (date = 1st of each month)
    year  → one point per calendar year, from the first year with data up to the
            current year, at most the last 10 years (date = 1 January)
    Future days/months in the window are included (they can hold prepaid appointments).
    revenue            = paid payment_amount (same rule as /api/payments/ total_paid)
    appointments_count = all appointments except cancelled
    """
    if chart_range == 'year':
        from django.db.models import Min
        first_dt   = Appointment.objects.aggregate(m=Min('date_time'))['m']
        first_year = timezone.localtime(first_dt).year if first_dt else today.year
        first_year = max(first_year, today.year - MAX_CHART_YEARS + 1)
        buckets = [datetime.date(y, 1, 1) for y in range(first_year, today.year + 1)]
        key_of  = lambda d: d.replace(month=1, day=1)
        end     = datetime.date(today.year + 1, 1, 1)
    elif chart_range == 'month':
        buckets = [datetime.date(today.year, m, 1) for m in range(1, 13)]
        key_of  = lambda d: d.replace(day=1)
        end     = datetime.date(today.year + 1, 1, 1)
    else:  # week
        monday  = today - datetime.timedelta(days=today.weekday())
        buckets = [monday + datetime.timedelta(days=i) for i in range(7)]
        key_of  = lambda d: d
        end     = monday + datetime.timedelta(days=7)

    points = {b: {'revenue': 0.0, 'appointments_count': 0} for b in buckets}
    rows = (
        Appointment.objects
        .filter(date_time__gte=_day_start(buckets[0]),
                date_time__lt=_day_start(end))
        .exclude(status='cancelled', payment_status='pending')
        .values_list('date_time', 'status', 'payment_status', 'payment_amount')
    )
    for dt, status, pay_status, amount in rows:
        key = key_of(timezone.localtime(dt).date())
        if key not in points:
            continue
        if status != 'cancelled':
            points[key]['appointments_count'] += 1
        if pay_status == 'paid' and amount:
            points[key]['revenue'] += float(amount)

    return [
        {'date': str(b), 'revenue': round(points[b]['revenue'], 2),
         'appointments_count': points[b]['appointments_count']}
        for b in buckets
    ]


def _to_min(t):
    return t.hour * 60 + t.minute


def _merge(intervals):
    """Merge overlapping (start, end) minute intervals."""
    out = []
    for s, e in sorted(i for i in intervals if i[1] > i[0]):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def _clip(intervals, lo, hi):
    return [(max(s, lo), min(e, hi)) for s, e in intervals if min(e, hi) > max(s, lo)]


def _length(intervals):
    return sum(e - s for s, e in _merge(intervals))


def _percentages(parts):
    """Integer percentages that always add up to 100 (largest remainder)."""
    total = sum(parts)
    if total <= 0:
        return [0] * len(parts)
    raw = [p * 100 / total for p in parts]
    floors = [int(r) for r in raw]
    order = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
    for i in order[:100 - sum(floors)]:
        floors[i] += 1
    return floors


def _today_occupancy(today):
    """
    Today's therapist schedule capacity split into:
      confirmed — minutes booked by non-cancelled appointments
      blocked   — staff breaks, staff on leave, clinic closed / planned closure
      available — everything else in the therapists' working hours
    """
    zero = {'confirmed_pct': 0, 'available_pct': 0, 'blocked_pct': 0}
    day_code = DAY_CODES[today.weekday()]

    shifts = list(
        StaffWorkingHours.objects
        .filter(day=day_code, staff__role='therapist', staff__is_active=True)
    )
    if not shifts:
        return zero

    clinic_day = ClinicHours.objects.filter(day=day_code).first()
    clinic_closed = (
        (clinic_day is not None and not clinic_day.is_open)
        or PlannedClosure.objects.filter(from_date__lte=today, to_date__gte=today).exists()
    )
    if clinic_day and clinic_day.is_open and clinic_day.open_time and clinic_day.close_time:
        clinic_window = (_to_min(clinic_day.open_time), _to_min(clinic_day.close_time))
    else:
        clinic_window = (0, 24 * 60)

    staff_ids = [s.staff_id for s in shifts]
    on_leave = set(
        StaffLeave.objects.filter(staff_id__in=staff_ids, from_date__lte=today, to_date__gte=today)
        .values_list('staff_id', flat=True)
    )
    breaks = {}
    for b in StaffBreakTime.objects.filter(staff_id__in=staff_ids):
        breaks.setdefault(b.staff_id, []).append((_to_min(b.start_time), _to_min(b.end_time)))
    booked = {}
    for a in Appointment.objects.filter(staff_id__in=staff_ids, date_time__date=today).exclude(status='cancelled'):
        start = timezone.localtime(a.date_time)
        s = start.hour * 60 + start.minute
        booked.setdefault(a.staff_id, []).append((s, s + (a.duration or 0)))

    total = confirmed = blocked = 0
    for shift in shifts:
        lo, hi = _to_min(shift.start_time), _to_min(shift.end_time)
        if not clinic_closed:
            lo, hi = max(lo, clinic_window[0]), min(hi, clinic_window[1])
        if hi <= lo:
            continue
        length = hi - lo
        total += length
        if clinic_closed or shift.staff_id in on_leave:
            blocked += length
            continue
        brk = _clip(breaks.get(shift.staff_id, []), lo, hi)
        appts = _clip(booked.get(shift.staff_id, []), lo, hi)
        b_len = _length(brk)
        blocked += b_len
        confirmed += _length(brk + appts) - b_len   # booked time not already counted as break

    if total == 0:
        return zero
    c, a, b = _percentages([confirmed, total - confirmed - blocked, blocked])
    return {'confirmed_pct': c, 'available_pct': a, 'blocked_pct': b}


def _reception_tasks(today):
    """Only 'confirm_appointments' for now: tomorrow's appointments still in 'upcoming' status."""
    tomorrow = today + datetime.timedelta(days=1)
    count = Appointment.objects.filter(date_time__date=tomorrow, status='upcoming').count()
    tasks = []
    if count:
        tasks.append({
            'type':  'confirm_appointments',
            'label': "Confirm tomorrow's appointments",
            'count': count,
        })
    return tasks


class DashboardView(APIView):
    """
    GET /api/dashboard/
    Returns the correct dashboard based on logged-in user role:
    - Admin     → full overview (revenue, leads, best services, staff performance)
    - Reception → today's stats (with % change), occupancy, today's revenue,
                  revenue chart, tasks + next up appointments
    Query params: ?chart_range=week|month|year  (default: month)
      week = Mon–Sun this week (daily) · month = Jan–Dec this year (monthly) · year = per year, up to 10
    - Therapist → my schedule (today's sessions, current session, next up)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = getattr(request.user, 'role', '')
        if role == 'therapist':
            return self._therapist_dashboard(request)
        elif role == 'reception':
            return self._reception_dashboard(request)
        else:
            return self._admin_dashboard(request)

    # ── Therapist Dashboard ───────────────────────────────────────────────────
    def _therapist_dashboard(self, request):
        today = timezone.localdate()
        now   = timezone.now()

        # Fetch therapist fresh from DB
        from users.models import User as UserModel
        try:
            therapist = UserModel.objects.get(pk=request.user.pk)
        except Exception:
            therapist = request.user

        appts = Appointment.objects.filter(
            staff=therapist,
            date_time__date=today
        ).select_related('patient', 'treatment', 'room_fk').order_by('date_time')

        total_today  = appts.count()
        completed    = appts.filter(status='completed').count()
        pending      = appts.filter(status='upcoming').count()

        # Current session — status changed to in_session
        current = appts.filter(
            status='in_session'
        ).order_by('date_time').first()

        # Next up — all today's upcoming appointments for this therapist
        next_up = appts.filter(
            status='upcoming'
        ).order_by('date_time')

        return Response({
            'role':     'therapist',
            'greeting': _get_greeting(),
            'name':     request.user.username or request.user.email.split('@')[0],
            'date':     str(today),
            'stats': {
                'todays_appointments': total_today,
                'completed_sessions':  completed,
                'pending_sessions':    pending,
            },
            'current_session': _fmt_appt(current) if current else None,
            'next_up':         [_fmt_appt(a) for a in next_up],
        })

    # ── Reception Dashboard ───────────────────────────────────────────────────
    def _reception_dashboard(self, request):
        today          = timezone.localdate()
        yesterday      = today - datetime.timedelta(days=1)
        start_of_month = _day_start(today.replace(day=1))
        chart_range    = _get_chart_range(request)

        todays_appts = Appointment.objects.filter(
            date_time__date=today
        ).select_related('patient', 'staff', 'treatment', 'room_fk')
        yesterdays_appts = Appointment.objects.filter(date_time__date=yesterday)

        next_up = Appointment.objects.filter(
            date_time__date=today,
            status='upcoming'
        ).select_related('patient', 'staff', 'treatment', 'room_fk').order_by('date_time')

        # All in_session appointments right now
        current_sessions = Appointment.objects.filter(
            date_time__date=today,
            status='in_session'
        ).select_related('patient', 'staff', 'treatment', 'room_fk').order_by('date_time')

        appts_today_count = todays_appts.count()
        checked_in_today  = todays_appts.filter(patient_arrived=True).count()
        cancelled_today   = todays_appts.filter(status='cancelled').count()

        return Response({
            'role':     'reception',
            'greeting': _get_greeting(),
            'name':     request.user.username or request.user.email.split('@')[0],
            'date':     str(today),
            # Kept unchanged for backward compatibility with the current app
            'stats': {
                'todays_appointments': appts_today_count,
                'checked_in':          checked_in_today,
                'cancelled':           cancelled_today,
                'in_session':          current_sessions.count(),
                'new_patients':        Patient.objects.filter(created_at__gte=start_of_month).count(),
            },
            # New design: every tile is {value, change_pct, trend} compared with yesterday
            'today': {
                'appointments': _calc_trend(appts_today_count, yesterdays_appts.count()),
                'checked_in':   _calc_trend(checked_in_today, yesterdays_appts.filter(patient_arrived=True).count()),
                'cancelled':    _calc_trend(cancelled_today, yesterdays_appts.filter(status='cancelled').count()),
                'new_patients': _calc_trend(
                    Patient.objects.filter(created_at__date=today).count(),
                    Patient.objects.filter(created_at__date=yesterday).count(),
                ),
                'occupancy':    _today_occupancy(today),
            },
            'revenue': {
                'today': _calc_trend(_revenue_total(todays_appts), _revenue_total(yesterdays_appts)),
            },
            'chart_range':      chart_range,
            'revenue_chart':    _build_revenue_chart(chart_range, today),
            'tasks':            _reception_tasks(today),
            'current_sessions': [_fmt_appt(a) for a in current_sessions],
            'next_up': [_fmt_appt(a) for a in next_up],
        })

    # ── Admin Dashboard ───────────────────────────────────────────────────────
    def _admin_dashboard(self, request):
        today            = timezone.localdate()
        yesterday        = today - datetime.timedelta(days=1)
        start_of_today   = _day_start(today)
        # Week  = last 7 days incl. today, vs the 7 days before
        # Month = this calendar month,     vs the previous calendar month
        #   → revenue.monthly matches GET /api/payments/?month=YYYY-MM stats.total_paid
        week_start         = today - datetime.timedelta(days=6)
        month_first, month_last = month_bounds(today)
        last_first, last_last   = month_bounds(month_first - datetime.timedelta(days=1))
        start_of_month   = _day_start(month_first)
        start_last_month = _day_start(last_first)
        end_last_month   = start_of_month

        all_appts        = Appointment.objects.all()
        appts_today      = in_dates(all_appts, today, today)
        appts_yesterday  = in_dates(all_appts, yesterday, yesterday)
        appts_week       = in_dates(all_appts, week_start, today)
        appts_prev_week  = in_dates(all_appts, week_start - datetime.timedelta(days=7), week_start - datetime.timedelta(days=1))
        appts_month      = in_dates(all_appts, month_first, month_last)
        appts_last_month = in_dates(all_appts, last_first, last_last)

        revenue = paid_total

        rev_today      = revenue(appts_today)
        rev_yesterday  = revenue(appts_yesterday)
        rev_week       = revenue(appts_week)
        rev_prev_week  = revenue(appts_prev_week)
        rev_month      = revenue(appts_month)
        rev_last_month = revenue(appts_last_month)

        # Today appointments trend
        total_today    = appts_today.count()
        total_yesterday = appts_yesterday.count()

        # Cancellation rate
        total_month  = appts_month.count()
        cancelled    = appts_month.filter(status='cancelled').count()
        cancel_curr  = round((cancelled / total_month * 100), 1) if total_month > 0 else 0
        total_lm     = appts_last_month.count()
        cancelled_lm = appts_last_month.filter(status='cancelled').count()
        cancel_prev  = round((cancelled_lm / total_lm * 100), 1) if total_lm > 0 else 0

        # Rebooking rate
        def rebooking(qs_filter):
            ret = (
                Appointment.objects.filter(**qs_filter)
                .values('patient').annotate(c=Count('id')).filter(c__gt=1).count()
            )
            tot = (
                Appointment.objects.filter(**qs_filter)
                .values('patient').distinct().count()
            )
            return round((ret / tot * 100), 1) if tot > 0 else 0

        rebook_curr = rebooking({'date_time__gte': start_of_month})
        rebook_prev = rebooking({'date_time__gte': start_last_month, 'date_time__lt': end_last_month})

        # Lead sources with marketing_source_id
        SOURCE_ID = {
            'instagram': 1, 'web': 2, 'walk_in': 3,
            'referral': 4, 'whatsapp': 5, 'other': 6,
        }
        SOURCE_LABEL = {
            'instagram': 'Instagram', 'web': 'Website', 'walk_in': 'Walk-in',
            'referral': 'Referral', 'whatsapp': 'WhatsApp', 'other': 'Other',
        }
        # Lead counts by source (string values)
        lead_counts = {
            s['source']: s['count']
            for s in Lead.objects.values('source').annotate(count=Count('id'))
        }
        # Map lead source string to ID
        LEAD_SOURCE_TO_ID = {
            'instagram': 1, 'web': 2, 'walk_in': 3,
            'referral': 4, 'whatsapp': 5, 'other': 6,
        }
        lead_by_id = {}
        for source, cnt in lead_counts.items():
            sid = LEAD_SOURCE_TO_ID.get(source, 6)
            lead_by_id[sid] = lead_by_id.get(sid, 0) + cnt

        # Patient counts by marketing_source (integer ID)
        patient_counts = {
            p['marketing_source']: p['count']
            for p in Patient.objects.filter(
                marketing_source__isnull=False
            ).values('marketing_source').annotate(count=Count('id'))
        }

        # Combine both
        lead_sources = [
            {
                'marketing_source_id': mid,
                'source':              src,
                'label':               SOURCE_LABEL[src],
                'lead_count':          lead_by_id.get(mid, 0),
                'patient_count':       patient_counts.get(mid, 0),
                'total':               lead_by_id.get(mid, 0) + patient_counts.get(mid, 0),
            }
            for src, mid in SOURCE_ID.items()
        ]

        # Best services — max 3
        best_services = list(
            appts_month
            .values('treatment__id', 'treatment__name', 'treatment__duration')
            .annotate(
                bookings=Count('id'),
                revenue=Sum('payment_amount', filter=Q(payment_status='paid'))
            )
            .order_by('-bookings')[:3]
        )

        # Staff performance
        staff_perf = []
        for s in User.objects.filter(role='therapist'):
            sa = appts_month.filter(staff=s)
            staff_perf.append({
                'staff_id':        s.id,
                'name':            s.username or s.email.split('@')[0],
                'profile_image':   s.profile_image or None,
                'specialist_area': s.specialist_area,
                'total':           sa.count(),
                'completed':       sa.filter(status='completed').count(),
                'revenue':         paid_total(sa),
            })
        staff_perf.sort(key=lambda x: x['revenue'], reverse=True)

        # Revenue chart — ?chart_range=week|month|year (default month = Jan–Dec this year)
        chart_range   = _get_chart_range(request)
        revenue_chart = _build_revenue_chart(chart_range, today)

        return Response({
            'role':     'admin',
            'greeting': _get_greeting(),
            'name':     request.user.username or request.user.email.split('@')[0],
            'date':     str(today),
            'revenue': {
                'today':      _calc_trend(rev_today, rev_yesterday),
                'weekly':     _calc_trend(rev_week, rev_prev_week),
                'monthly':    _calc_trend(rev_month, rev_last_month),
            },
            'today': {
                'appointments': _calc_trend(total_today, total_yesterday),
                'checked_in':   appts_today.filter(patient_arrived=True).count(),
                'cancelled':    appts_today.filter(status='cancelled').count(),
                'new_patients': Patient.objects.filter(created_at__gte=start_of_today).count(),
            },
            'appointments': {
                'this_month': total_month,
                'completed':  appts_month.filter(status='completed').count(),
                'cancelled':  cancelled,
            },
            'cancellation_rate': _calc_trend(cancel_curr, cancel_prev),
            'rebooking_rate':    _calc_trend(rebook_curr, rebook_prev),
            'patients': {
                'total':          Patient.objects.count(),
                'new_this_month': Patient.objects.filter(created_at__gte=start_of_month).count(),
                'returning':      Patient.objects.filter(category='Returning').count(),
                'vip':            Patient.objects.filter(category='VIP').count(),
            },
            'leads': {
                'total':     Lead.objects.count(),
                'active':    Lead.objects.filter(stage__in=['new_inquiries','engaged','consultation']).count(),
                'converted': Lead.objects.filter(stage='converted').count(),
                'valuation': float(Lead.objects.aggregate(t=Sum('value'))['t'] or 0),
                'by_marketing_source': lead_sources,
            },
            'best_services': [
                {
                    'treatment_id': s['treatment__id'],
                    'name':         s['treatment__name'],
                    'duration':     s['treatment__duration'],
                    'bookings':     s['bookings'],
                    'revenue':      float(s['revenue'] or 0),
                }
                for s in best_services
            ],
            'staff_performance': staff_perf,
            'chart_range':       chart_range,
            'revenue_chart':     revenue_chart,
        })


# Keep individual endpoints for direct access
class ReceptionDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return DashboardView()._reception_dashboard(request)


class TherapistDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return DashboardView()._therapist_dashboard(request)


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return DashboardView()._admin_dashboard(request)