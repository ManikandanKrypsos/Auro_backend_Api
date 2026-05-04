from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Q
import datetime
from appointments.models import Appointment
from patients.models import Patient
from treatments.models import Treatment
from leads.models import Lead
from users.models import User
from users.permissions import IsAdmin, IsAdminOrReception


class ReceptionDashboardView(APIView):
    """
    GET /api/dashboard/reception/
    Reception dashboard — today's stats + next up appointments.
    Shows: today's appointments, checked in, cancelled, new patients, next up.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        today = timezone.localdate()
        now   = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Today's appointments
        todays_appts = Appointment.objects.filter(
            date_time__date=today
        ).select_related('patient', 'staff', 'treatment', 'room_fk')

        # Stats
        total_today  = todays_appts.count()
        checked_in   = todays_appts.filter(patient_arrived=True).count()
        cancelled    = todays_appts.filter(status='cancelled').count()
        new_patients = Patient.objects.filter(
            created_at__gte=start_of_month
        ).count()

        # Next up — upcoming appointments from now, ordered by time
        next_up = Appointment.objects.filter(
            date_time__date=today,
            date_time__gte=now,
            status='upcoming'
        ).select_related(
            'patient', 'staff', 'treatment', 'room_fk'
        ).order_by('date_time')[:5]

        def fmt_appt(a):
            return {
                'id':            a.id,
                'time':          a.date_time.strftime('%I:%M %p') if a.date_time else None,
                'patient_name':  a.patient.name if a.patient else None,
                'treatment':     a.treatment.name if a.treatment else None,
                'staff_name':    a.staff.username if a.staff else None,
                'duration':      a.duration,
                'room':          a.room_fk.name if a.room_fk else None,
                'status':        a.status,
                'patient_arrived': a.patient_arrived,
                'consent_status':  a.consent_status,
            }

        return Response({
            'greeting':  _get_greeting(),
            'staff_name': request.user.username or request.user.email.split('@')[0],
            'date':       str(today),
            'stats': {
                'todays_appointments': total_today,
                'checked_in':          checked_in,
                'cancelled':           cancelled,
                'new_patients':        new_patients,
            },
            'next_up': [fmt_appt(a) for a in next_up],
        })


def _get_greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return 'Good Morning'
    elif hour < 17:
        return 'Good Afternoon'
    return 'Good Evening'


class DashboardOverviewView(APIView):
    """
    GET /api/dashboard/
    Full admin dashboard — revenue, patients, appointments, leads.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        now   = timezone.now()

        start_of_today      = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_month      = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - datetime.timedelta(days=1)).replace(day=1)

        appts_today      = Appointment.objects.filter(date_time__date=today)
        appts_month      = Appointment.objects.filter(date_time__gte=start_of_month)
        appts_last_month = Appointment.objects.filter(
            date_time__gte=start_of_last_month,
            date_time__lt=start_of_month
        )

        def get_revenue(qs):
            return float(
                qs.filter(status='completed')
                  .aggregate(total=Sum('payment_amount'))['total'] or 0
            )

        revenue_today      = get_revenue(appts_today)
        revenue_this_month = get_revenue(appts_month)
        revenue_last_month = get_revenue(appts_last_month)
        revenue_growth     = 0
        if revenue_last_month > 0:
            revenue_growth = round(
                ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100, 1
            )

        total_patients = Patient.objects.count()
        new_this_month = Patient.objects.filter(created_at__gte=start_of_month).count()

        total_this_month  = appts_month.count()
        completed_month   = appts_month.filter(status='completed').count()
        cancelled_month   = appts_month.filter(status='cancelled').count()
        cancellation_rate = round((cancelled_month / total_this_month * 100), 1) if total_this_month > 0 else 0

        total_leads     = Lead.objects.count()
        new_leads_month = Lead.objects.filter(created_at__gte=start_of_month).count()
        converted_leads = Lead.objects.filter(stage='converted').count()
        conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0

        # Today's summary
        checked_in   = appts_today.filter(patient_arrived=True).count()
        new_patients = Patient.objects.filter(created_at__gte=start_of_today).count()

        return Response({
            'greeting':   _get_greeting(),
            'staff_name': request.user.username or request.user.email.split('@')[0],
            'date':       str(today),
            'today': {
                'appointments': appts_today.count(),
                'checked_in':   checked_in,
                'cancelled':    appts_today.filter(status='cancelled').count(),
                'new_patients': new_patients,
            },
            'revenue': {
                'today':      revenue_today,
                'this_month': revenue_this_month,
                'last_month': revenue_last_month,
                'growth':     f'{revenue_growth}%',
            },
            'appointments': {
                'today':             appts_today.count(),
                'this_month':        total_this_month,
                'completed_month':   completed_month,
                'cancelled_month':   cancelled_month,
                'cancellation_rate': f'{cancellation_rate}%',
            },
            'patients': {
                'total':          total_patients,
                'new_this_month': new_this_month,
            },
            'leads': {
                'total':           total_leads,
                'new_this_month':  new_leads_month,
                'converted':       converted_leads,
                'conversion_rate': f'{conversion_rate}%',
            },
        })


class BestServicesView(APIView):
    """
    GET /api/dashboard/best-services/
    Top treatments by bookings this month.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        now            = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        services = (
            Appointment.objects
            .filter(date_time__gte=start_of_month)
            .values('treatment__id', 'treatment__name', 'treatment__duration')
            .annotate(
                total_bookings=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
                cancelled=Count('id', filter=Q(status='cancelled')),
                revenue=Sum('payment_amount', filter=Q(status='completed')),
            )
            .order_by('-total_bookings')
        )

        result = []
        for s in services:
            result.append({
                'treatment_id':   s['treatment__id'],
                'treatment':      s['treatment__name'],
                'duration':       s['treatment__duration'],
                'total_bookings': s['total_bookings'],
                'completed':      s['completed'],
                'cancelled':      s['cancelled'],
                'revenue':        float(s['revenue'] or 0),
            })

        return Response({'best_services': result})


class StaffPerformanceView(APIView):
    """
    GET /api/dashboard/staff-performance/
    Sessions, cancellations and revenue per therapist this month.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        now            = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        staff_list     = User.objects.filter(role='therapist')
        result         = []

        for staff in staff_list:
            appts     = Appointment.objects.filter(staff=staff, date_time__gte=start_of_month)
            completed = appts.filter(status='completed')
            cancelled = appts.filter(status='cancelled').count()
            total     = appts.count()
            revenue   = float(
                completed.aggregate(total=Sum('payment_amount'))['total'] or 0
            )
            completion_rate = round((completed.count() / total * 100), 1) if total > 0 else 0

            result.append({
                'staff_id':        staff.id,
                'name':            staff.username or staff.email.split('@')[0],
                'profile_image':   staff.profile_image or None,
                'specialist_area': staff.specialist_area,
                'total_sessions':  total,
                'completed':       completed.count(),
                'cancelled':       cancelled,
                'completion_rate': f'{completion_rate}%',
                'revenue':         revenue,
            })

        result.sort(key=lambda x: x['revenue'], reverse=True)
        return Response({'staff_performance': result})


class RevenueChartView(APIView):
    """
    GET /api/dashboard/revenue-chart/
    Daily revenue for last 30 days.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        days  = []

        for i in range(29, -1, -1):
            day     = today - datetime.timedelta(days=i)
            revenue = float(
                Appointment.objects
                .filter(date_time__date=day, status='completed')
                .aggregate(total=Sum('payment_amount'))['total'] or 0
            )
            days.append({'date': str(day), 'revenue': revenue})

        return Response({'last_30_days': days})


class RebookingRateView(APIView):
    """
    GET /api/dashboard/rebooking-rate/
    How many patients came back this month.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        now            = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        returning = (
            Appointment.objects
            .filter(date_time__gte=start_of_month)
            .values('patient')
            .annotate(visit_count=Count('id'))
            .filter(visit_count__gt=1)
            .count()
        )
        total_patients_this_month = (
            Appointment.objects
            .filter(date_time__gte=start_of_month)
            .values('patient')
            .distinct()
            .count()
        )
        rebooking_rate = round(
            (returning / total_patients_this_month * 100), 1
        ) if total_patients_this_month > 0 else 0

        return Response({
            'total_patients_this_month': total_patients_this_month,
            'returning_patients':        returning,
            'rebooking_rate':            f'{rebooking_rate}%',
        })