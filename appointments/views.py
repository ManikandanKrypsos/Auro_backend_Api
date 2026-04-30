import datetime
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin, IsAdminOrReception
from .models import Appointment
from .serializers import AppointmentSerializer, AppointmentWriteSerializer
from users.models import User
from treatments.models import Treatment


def _get_available_slots(staff, date, duration):
    """
    Generate 30-min slots from 9AM-5PM, remove already booked ones.
    """
    slot_start  = datetime.datetime.combine(date, datetime.time(9, 0))
    slot_end    = datetime.datetime.combine(date, datetime.time(17, 0))
    slot_gap    = datetime.timedelta(minutes=30)
    dur_delta   = datetime.timedelta(minutes=duration)

    booked = Appointment.objects.filter(
        staff=staff,
        date_time__date=date,
        status__in=['upcoming']
    ).values_list('date_time', 'duration')

    booked_ranges = [
        (dt, dt + datetime.timedelta(minutes=d))
        for dt, d in booked
    ]

    slots   = []
    current = slot_start
    while current + dur_delta <= slot_end:
        end = current + dur_delta
        conflict = any(
            not (end <= bs or current >= be)
            for bs, be in booked_ranges
        )
        if not conflict:
            slots.append(current.strftime('%I:%M %p').lstrip('0'))
        current += slot_gap

    return slots


class AppointmentListView(APIView):
    """
    GET  /api/appointments/           — list all appointments
         ?date=2026-04-30             filter by date
         ?date_from=2026-04-01        filter range start
         ?date_to=2026-04-30          filter range end
         ?staff_id=8                  filter by staff
         ?status=upcoming             filter by status
         ?search=patient_name         search by patient name
         ?today=true                  today's appointments only

    POST /api/appointments/           — create appointment
    """
    def get_permissions(self):
        return [IsAdminOrReception()] if self.request.method == 'POST' else [IsAuthenticated()]

    def get(self, request):
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room', 'price_plan'
        ).all()

        user = request.user
        if user.role == 'therapist':
            qs = qs.filter(staff=user)

        today    = request.query_params.get('today')
        date     = request.query_params.get('date')
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')
        staff_id  = request.query_params.get('staff_id')
        status    = request.query_params.get('status')
        search    = request.query_params.get('search', '').strip()

        if today == 'true':
            today_date = timezone.now().date()
            qs = qs.filter(date_time__date=today_date)
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
        if staff_id:
            qs = qs.filter(staff__id=staff_id)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(patient__name__icontains=search) | \
                 qs.filter(treatment__name__icontains=search)

        return Response(AppointmentSerializer(qs, many=True).data)

    def post(self, request):
        serializer = AppointmentWriteSerializer(data=request.data)
        if serializer.is_valid():
            appt = serializer.save()
            # Trigger celery tasks if available
            try:
                from .tasks import send_booking_confirmation
                send_booking_confirmation.delay(appt.id)
            except Exception:
                pass
            return Response(AppointmentSerializer(appt).data, status=201)
        return Response(serializer.errors, status=400)


class AppointmentDetailView(APIView):
    """
    GET    /api/appointments/<id>/
    PATCH  /api/appointments/<id>/
    DELETE /api/appointments/<id>/
    """
    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAdminOrReception()]
        return [IsAuthenticated()]

    def _get(self, pk):
        try:
            return Appointment.objects.select_related(
                'patient', 'staff', 'treatment', 'room', 'price_plan'
            ).get(pk=pk)
        except Appointment.DoesNotExist:
            return None

    def get(self, request, pk):
        appt = self._get(pk)
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)
        return Response(AppointmentSerializer(appt).data)

    def _update(self, request, pk):
        appt = self._get(pk)
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)
        serializer = AppointmentWriteSerializer(appt, data=request.data, partial=True)
        if serializer.is_valid():
            appt = serializer.save()
            return Response(AppointmentSerializer(appt).data)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        return self._update(request, pk)

    def put(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        appt = self._get(pk)
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)
        appt.delete()
        return Response({'message': 'Appointment deleted.'})


class AppointmentStatusView(APIView):
    """
    PATCH /api/appointments/<id>/status/
    Body: { "status": "completed" }
    Status options: upcoming | completed | cancelled | no_show
    """
    permission_classes = [IsAdminOrReception]

    def patch(self, request, pk):
        try:
            appt = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        status = request.data.get('status')
        valid  = ['upcoming', 'completed', 'cancelled', 'no_show']
        if status not in valid:
            return Response({'error': f'Status must be one of: {valid}'}, status=400)

        appt.status = status
        appt.save()
        return Response(AppointmentSerializer(appt).data)


class AppointmentArrivalView(APIView):
    """
    PATCH /api/appointments/<id>/arrived/
    Body: { "patient_arrived": true }
    Marks patient as arrived.
    """
    permission_classes = [IsAdminOrReception]

    def patch(self, request, pk):
        try:
            appt = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        appt.patient_arrived = request.data.get('patient_arrived', True)
        appt.save()
        return Response({
            'message':         'Patient arrival status updated.',
            'patient_arrived': appt.patient_arrived,
        })


class AppointmentConsentView(APIView):
    """
    PATCH /api/appointments/<id>/consent/
    Body: { "consent_status": "signed", "consent_form_url": "https://..." }
    """
    permission_classes = [IsAdminOrReception]

    def patch(self, request, pk):
        try:
            appt = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        status = request.data.get('consent_status')
        url    = request.data.get('consent_form_url', '')

        if status and status not in ['pending', 'signed']:
            return Response({'error': 'consent_status must be pending or signed.'}, status=400)

        if status:
            appt.consent_status = status
        if url:
            appt.consent_form_url = url
        appt.save()
        return Response({
            'message':         'Consent updated.',
            'consent_status':  appt.consent_status,
            'consent_form_url': appt.consent_form_url,
        })


class AvailableSlotsView(APIView):
    """
    GET /api/appointments/available-slots/
    ?staff_id=8&date=2026-04-30&duration=60

    Returns available time slots for booking.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        staff_id = request.query_params.get('staff_id')
        date_str = request.query_params.get('date')
        duration = int(request.query_params.get('duration', 60))

        if not staff_id or not date_str:
            return Response({'error': 'staff_id and date are required.'}, status=400)

        try:
            staff = User.objects.get(id=staff_id, role__in=['therapist', 'reception'])
        except User.DoesNotExist:
            return Response({'error': 'Staff not found.'}, status=404)

        date = parse_date(date_str)
        if not date:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        slots = _get_available_slots(staff, date, duration)
        return Response({
            'staff_id': int(staff_id),
            'date':     date_str,
            'duration': duration,
            'slots':    slots,
        })


class TodayAppointmentsView(APIView):
    """
    GET /api/appointments/today/
    Returns today's appointments grouped by status.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room'
        ).filter(date_time__date=today)

        if request.user.role == 'therapist':
            qs = qs.filter(staff=request.user)

        status = request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        return Response({
            'date':             str(today),
            'total':            qs.count(),
            'upcoming':         qs.filter(status='upcoming').count(),
            'completed':        qs.filter(status='completed').count(),
            'cancelled':        qs.filter(status='cancelled').count(),
            'appointments':     AppointmentSerializer(qs, many=True).data,
        })


class CalendarView(APIView):
    """
    GET /api/appointments/calendar/
    ?date=2026-04-30     appointments for that day
    ?week=2026-04-28     appointments for the week starting that date
    ?month=2026-04       appointments for the whole month
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room'
        ).all()

        if request.user.role == 'therapist':
            qs = qs.filter(staff=request.user)

        date  = request.query_params.get('date')
        week  = request.query_params.get('week')
        month = request.query_params.get('month')

        if date:
            parsed = parse_date(date)
            if parsed:
                qs = qs.filter(date_time__date=parsed)
                return Response({
                    'date':             str(parsed),
                    'total':            qs.count(),
                    'appointments':     AppointmentSerializer(qs, many=True).data,
                })

        if week:
            parsed = parse_date(week)
            if parsed:
                week_end = parsed + datetime.timedelta(days=7)
                qs = qs.filter(date_time__date__gte=parsed, date_time__date__lt=week_end)
                return Response({
                    'week_start':   str(parsed),
                    'week_end':     str(week_end),
                    'total':        qs.count(),
                    'appointments': AppointmentSerializer(qs, many=True).data,
                })

        if month:
            try:
                year, mon = map(int, month.split('-'))
                qs = qs.filter(date_time__year=year, date_time__month=mon)
                return Response({
                    'month':        month,
                    'total':        qs.count(),
                    'appointments': AppointmentSerializer(qs, many=True).data,
                })
            except Exception:
                return Response({'error': 'Invalid month format. Use YYYY-MM.'}, status=400)

        return Response({'error': 'Provide date, week, or month param.'}, status=400)