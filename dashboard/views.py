from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
import datetime

from appointments.models import Appointment
from patients.models import Patient
from treatments.models import Treatment
from leads.models import Lead
from users.models import User
from users.permissions import IsAdmin


class DashboardOverviewView(APIView):
    """
    GET /api/dashboard/
    Full owner dashboard — revenue, patients, appointments, leads.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        now = timezone.now()

        # ── Time ranges ───────────────────────────────
        start_of_today    = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week     = now - datetime.timedelta(days=now.weekday())
        start_of_month    = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - datetime.timedelta(days=1)).replace(day=1)

        # ── Appointments ──────────────────────────────
        appts_today    = Appointment.objects.filter(date_time__date=today)
        appts_month    = Appointment.objects.filter(date_time__gte=start_of_month)
        appts_last_month = Appointment.objects.filter(
            date_time__gte=start_of_last_month,
            date_time__lt=start_of_month
        )

        # ── Revenue (sum of treatment prices) ─────────
        def get_revenue(qs):
            return float(
                qs.filter(status='completed')
                  .aggregate(total=Sum('treatment__price'))['total'] or 0
            )

        revenue_today      = get_revenue(appts_today)
        revenue_this_month = get_revenue(appts_month)
        revenue_last_month = get_revenue(appts_last_month)
        revenue_growth     = 0
        if revenue_last_month > 0:
            revenue_growth = round(
                ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100, 1
            )

        # ── Patients ──────────────────────────────────
        total_patients    = Patient.objects.count()
        new_this_month    = Patient.objects.filter(created_at__gte=start_of_month).count()
        vip_patients      = Patient.objects.filter(tags__icontains='VIP').count()

        # ── Appointment stats ─────────────────────────
        total_this_month   = appts_month.count()
        completed_month    = appts_month.filter(status='completed').count()
        cancelled_month    = appts_month.filter(status='cancelled').count()
        cancellation_rate  = round((cancelled_month / total_this_month * 100), 1) if total_this_month > 0 else 0

        # ── Leads ─────────────────────────────────────
        total_leads      = Lead.objects.count()
        new_leads_month  = Lead.objects.filter(created_at__gte=start_of_month).count()
        converted_leads  = Lead.objects.filter(stage__in=['booked', 'returning', 'vip']).count()
        conversion_rate  = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0

        return Response({
            'revenue': {
                'today':        revenue_today,
                'this_month':   revenue_this_month,
                'last_month':   revenue_last_month,
                'growth':       f'{revenue_growth}%',
            },
            'appointments': {
                'today':             appts_today.count(),
                'this_month':        total_this_month,
                'completed_month':   completed_month,
                'cancelled_month':   cancelled_month,
                'cancellation_rate': f'{cancellation_rate}%',
            },
            'patients': {
                'total':         total_patients,
                'new_this_month': new_this_month,
                'vip':           vip_patients,
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
    Top treatments by bookings and revenue.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)

        services = (
            Appointment.objects
            .filter(date_time__gte=start_of_month)
            .values('treatment__name', 'treatment__price')
            .annotate(
                total_bookings=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
                cancelled=Count('id', filter=Q(status='cancelled')),
            )
            .order_by('-total_bookings')
        )

        result = []
        for s in services:
            revenue = float(s['treatment__price'] or 0) * s['completed']
            result.append({
                'treatment':      s['treatment__name'],
                'price':          float(s['treatment__price'] or 0),
                'total_bookings': s['total_bookings'],
                'completed':      s['completed'],
                'cancelled':      s['cancelled'],
                'revenue':        revenue,
            })

        return Response({'best_services': result})


class StaffPerformanceView(APIView):
    """
    GET /api/dashboard/staff-performance/
    Sessions completed, cancellations and revenue per therapist.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)

        staff_list = User.objects.filter(role='therapist')
        result = []

        for staff in staff_list:
            appts = Appointment.objects.filter(
                staff=staff,
                date_time__gte=start_of_month
            )
            completed  = appts.filter(status='completed')
            cancelled  = appts.filter(status='cancelled').count()
            total      = appts.count()
            revenue    = float(
                completed.aggregate(total=Sum('treatment__price'))['total'] or 0
            )
            completion_rate = round((completed.count() / total * 100), 1) if total > 0 else 0

            result.append({
                'staff_id':        staff.id,
                'name':            staff.username,
                'email':           staff.email,
                'total_sessions':  total,
                'completed':       completed.count(),
                'cancelled':       cancelled,
                'completion_rate': f'{completion_rate}%',
                'revenue':         revenue,
            })

        # Sort by revenue descending
        result.sort(key=lambda x: x['revenue'], reverse=True)
        return Response({'staff_performance': result})


class RevenueChartView(APIView):
    """
    GET /api/dashboard/revenue-chart/
    Daily revenue for the last 30 days — ready for Flutter charts.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        days = []

        for i in range(29, -1, -1):
            day = today - datetime.timedelta(days=i)
            revenue = float(
                Appointment.objects
                .filter(date_time__date=day, status='completed')
                .aggregate(total=Sum('treatment__price'))['total'] or 0
            )
            days.append({
                'date':    str(day),
                'revenue': revenue,
            })

        return Response({'last_30_days': days})


class RebookingRateView(APIView):
    """
    GET /api/dashboard/rebooking-rate/
    How many patients came back for a second appointment.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)

        # Patients with more than 1 appointment this month
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