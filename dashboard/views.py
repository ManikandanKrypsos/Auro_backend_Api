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
from users.models import User


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


class DashboardView(APIView):
    """
    GET /api/dashboard/
    Returns the correct dashboard based on logged-in user role:
    - Admin     → full overview (revenue, leads, best services, staff performance)
    - Reception → today's stats + next up appointments
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
        now            = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        todays_appts = Appointment.objects.filter(
            date_time__date=today
        ).select_related('patient', 'staff', 'treatment', 'room_fk')

        next_up = Appointment.objects.filter(
            date_time__date=today,
            status='upcoming'
        ).select_related('patient', 'staff', 'treatment', 'room_fk').order_by('date_time')

        return Response({
            'role':     'reception',
            'greeting': _get_greeting(),
            'name':     request.user.username or request.user.email.split('@')[0],
            'date':     str(today),
            'stats': {
                'todays_appointments': todays_appts.count(),
                'checked_in':          todays_appts.filter(patient_arrived=True).count(),
                'cancelled':           todays_appts.filter(status='cancelled').count(),
                'new_patients':        Patient.objects.filter(created_at__gte=start_of_month).count(),
            },
            'next_up': [_fmt_appt(a) for a in next_up],
        })

    # ── Admin Dashboard ───────────────────────────────────────────────────────
    def _admin_dashboard(self, request):
        today            = timezone.localdate()
        now              = timezone.now()
        yesterday        = today - datetime.timedelta(days=1)
        start_of_today   = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week    = now - datetime.timedelta(days=7)
        start_of_month   = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_last_month = (start_of_month - datetime.timedelta(days=1)).replace(day=1)
        end_last_month   = start_of_month

        appts_today      = Appointment.objects.filter(date_time__date=today)
        appts_yesterday  = Appointment.objects.filter(date_time__date=yesterday)
        appts_week       = Appointment.objects.filter(date_time__gte=start_of_week)
        appts_prev_week  = Appointment.objects.filter(
            date_time__gte=start_of_week - datetime.timedelta(days=7),
            date_time__lt=start_of_week
        )
        appts_month      = Appointment.objects.filter(date_time__gte=start_of_month)
        appts_last_month = Appointment.objects.filter(
            date_time__gte=start_last_month,
            date_time__lt=end_last_month
        )

        def revenue(qs):
            return float(qs.filter(status='completed').aggregate(t=Sum('payment_amount'))['t'] or 0)

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
            Appointment.objects.filter(date_time__gte=start_of_month)
            .values('treatment__id', 'treatment__name', 'treatment__duration')
            .annotate(
                bookings=Count('id'),
                revenue=Sum('payment_amount', filter=Q(status='completed'))
            )
            .order_by('-bookings')[:3]
        )

        # Staff performance
        staff_perf = []
        for s in User.objects.filter(role='therapist'):
            sa = Appointment.objects.filter(staff=s, date_time__gte=start_of_month)
            staff_perf.append({
                'staff_id':        s.id,
                'name':            s.username or s.email.split('@')[0],
                'profile_image':   s.profile_image or None,
                'specialist_area': s.specialist_area,
                'total':           sa.count(),
                'completed':       sa.filter(status='completed').count(),
                'revenue':         float(sa.filter(status='completed').aggregate(t=Sum('payment_amount'))['t'] or 0),
            })
        staff_perf.sort(key=lambda x: x['revenue'], reverse=True)

        # Revenue chart — last 30 days
        revenue_chart = []
        for i in range(29, -1, -1):
            day = today - datetime.timedelta(days=i)
            revenue_chart.append({
                'date':    str(day),
                'revenue': float(
                    Appointment.objects.filter(date_time__date=day, status='completed')
                    .aggregate(t=Sum('payment_amount'))['t'] or 0
                ),
            })

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
                'active':    Lead.objects.filter(stage__in=['new_inquiries','engaged','consultation','winning']).count(),
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