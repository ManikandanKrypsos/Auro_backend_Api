from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Q, Count
import datetime

from appointments.models import Appointment
from patients.models import Patient
from users.models import User
from appointments.serializers import AppointmentSerializer


class TherapistAppointmentsView(APIView):
    """
    GET /api/therapist/appointments/
    Returns ONLY appointments assigned to the logged-in therapist.

    Filters:
    ?today=true
    ?date=2026-05-06
    ?status=upcoming|completed|cancelled
    ?search=patient_name
    ?date_from=2026-05-01&date_to=2026-05-31
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get therapist from DB fresh — don't rely on JWT cached user
        try:
            therapist = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        # Base queryset — strictly filtered to this therapist
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room_fk', 'price_plan'
        ).filter(staff=therapist)

        # Apply filters
        today_param = request.query_params.get('today')
        date        = request.query_params.get('date')
        date_from   = request.query_params.get('date_from')
        date_to     = request.query_params.get('date_to')
        status      = request.query_params.get('status')
        search      = request.query_params.get('search', '').strip()
        consent     = request.query_params.get('consent_status')
        payment_st  = request.query_params.get('payment_status')

        if today_param == 'true':
            qs = qs.filter(date_time__date=timezone.now().date())
        if date:
            parsed = parse_date(date)
            if parsed:
                qs = qs.filter(date_time__date=parsed)
        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                qs = qs.filter(date_time__date__gte=parsed)
        if date_to:
            parsed = parse_date(date_to)
            if parsed:
                qs = qs.filter(date_time__date__lte=parsed)
        if status:
            qs = qs.filter(status=status)
        if consent:
            qs = qs.filter(consent_status=consent)
        if payment_st:
            qs = qs.filter(payment_status=payment_st)
        if search:
            qs = qs.filter(
                Q(patient__name__icontains=search) |
                Q(treatment__name__icontains=search)
            )

        qs = qs.order_by('date_time')
        return Response(AppointmentSerializer(qs, many=True).data)


class TherapistTodayView(APIView):
    """
    GET /api/therapist/today/
    Today's summary for the logged-in therapist.
    Returns: total, completed, pending, current session, next up.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            therapist = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        today = timezone.localdate()
        now   = timezone.now()

        appts = Appointment.objects.select_related(
            'patient', 'treatment', 'room_fk'
        ).filter(staff=therapist, date_time__date=today).order_by('date_time')

        total     = appts.count()
        completed = appts.filter(status='completed').count()
        pending   = appts.filter(status='upcoming').count()

        # Current session — patient_arrived=True and still upcoming
        current = appts.filter(
            patient_arrived=True,
            status='upcoming'
        ).order_by('date_time').first()

        # Next up
        next_up = appts.filter(
            date_time__gt=now,
            status='upcoming'
        ).order_by('date_time')[:5]

        def fmt(a):
            from django.utils import timezone as tz
            dt = tz.localtime(a.date_time) if a.date_time and tz.is_aware(a.date_time) else a.date_time
            return {
                'id':              a.id,
                'time':            dt.strftime('%I:%M %p') if dt else None,
                'patient_name':    a.patient.name if a.patient else None,
                'patient_id':      a.patient.patient_id if a.patient else None,
                'treatment':       a.treatment.name if a.treatment else None,
                'duration':        a.duration,
                'room':            a.room_fk.name if a.room_fk else None,
                'status':          a.status,
                'patient_arrived': a.patient_arrived,
                'consent_status':  a.consent_status,
            }

        return Response({
            'date':            str(today),
            'therapist_id':    therapist.id,
            'therapist_name':  therapist.username or therapist.email.split('@')[0],
            'stats': {
                'todays_appointments': total,
                'completed_sessions':  completed,
                'pending_sessions':    pending,
            },
            'current_session': fmt(current) if current else None,
            'next_up':         [fmt(a) for a in next_up],
        })


class TherapistPatientsView(APIView):
    """
    GET /api/therapist/patients/
    Returns ONLY patients who have had appointments with the logged-in therapist.

    Filters:
    ?search=name
    ?category=New|Returning|VIP
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            therapist = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        # Get patient IDs from this therapist's appointments only
        patient_ids = Appointment.objects.filter(
            staff=therapist
        ).values_list('patient_id', flat=True).distinct()

        qs = Patient.objects.filter(
            id__in=patient_ids
        ).order_by('-created_at')

        search   = request.query_params.get('search', '').strip()
        category = request.query_params.get('category', '').strip()

        if search:
            qs = qs.filter(
                Q(name__icontains=search)       |
                Q(phone__istartswith=search)    |
                Q(email__istartswith=search)    |
                Q(patient_id__icontains=search)
            )
        if category:
            qs = qs.filter(category=category)

        from patients.serializers import PatientSerializer
        return Response(PatientSerializer(qs, many=True).data)


class TherapistScheduleView(APIView):
    """
    GET /api/therapist/schedule/
    Returns appointments for a date range for the logged-in therapist.

    ?start_date=2026-05-01&end_date=2026-05-31
    ?date=2026-05-06  (single day)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            therapist = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        qs = Appointment.objects.select_related(
            'patient', 'treatment', 'room_fk', 'price_plan'
        ).filter(staff=therapist).order_by('date_time')

        date       = request.query_params.get('date')
        start_date = request.query_params.get('start_date')
        end_date   = request.query_params.get('end_date')

        if date:
            parsed = parse_date(date)
            if parsed:
                qs = qs.filter(date_time__date=parsed)
                return Response({
                    'date':         str(parsed),
                    'total':        qs.count(),
                    'appointments': AppointmentSerializer(qs, many=True).data,
                })

        if start_date and end_date:
            ps = parse_date(start_date)
            pe = parse_date(end_date)
            if ps and pe:
                qs = qs.filter(date_time__date__gte=ps, date_time__date__lte=pe)

                # Group by date
                grouped = {}
                for appt in qs:
                    day = str(appt.date_time.date())
                    if day not in grouped:
                        grouped[day] = []
                    grouped[day].append(AppointmentSerializer(appt).data)

                result = []
                current = ps
                while current <= pe:
                    day_str = str(current)
                    result.append({
                        'date':         day_str,
                        'total':        len(grouped.get(day_str, [])),
                        'appointments': grouped.get(day_str, []),
                    })
                    current += datetime.timedelta(days=1)

                return Response({
                    'start_date': str(ps),
                    'end_date':   str(pe),
                    'total':      qs.count(),
                    'days':       result,
                })

        return Response({'error': 'Provide date or start_date and end_date.'}, status=400)