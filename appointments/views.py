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


def _build_month_availability(staff, treatment, month_str, room=None):
    """
    Build full month availability for a staff + treatment + optional room.
    Returns list of date objects with slots.
    """
    import calendar
    from users.models import User
    from users.models import StaffWorkingHours, StaffLeave

    duration = treatment.duration
    dur_delta = datetime.timedelta(minutes=duration)
    today = datetime.date.today()
    now   = datetime.datetime.now()

    # Parse month
    year, month = map(int, month_str.split('-'))
    _, days_in_month = calendar.monthrange(year, month)

    # Build staff working hours dict: {day_abbr: (start_time, end_time)}
    working_hours = {
        wh.day: (wh.start_time, wh.end_time)
        for wh in StaffWorkingHours.objects.filter(staff=staff)
    }

    # Build staff leaves set: set of dates
    leave_dates = set()
    for leave in StaffLeave.objects.filter(staff=staff):
        d = leave.from_date
        while d <= leave.to_date:
            leave_dates.add(d)
            d += datetime.timedelta(days=1)

    # Booked appointments for staff this month
    staff_booked = Appointment.objects.filter(
        staff=staff,
        date_time__year=year,
        date_time__month=month,
        status='upcoming'
    ).values_list('date_time', 'duration')
    staff_booked_ranges = [
        (dt.replace(tzinfo=None) if dt.tzinfo else dt,
         (dt.replace(tzinfo=None) if dt.tzinfo else dt) + datetime.timedelta(minutes=d))
        for dt, d in staff_booked
    ]

    # Room booked appointments this month
    room_booked_ranges = []
    if room:
        room_booked = Appointment.objects.filter(
            room_fk=room,
            date_time__year=year,
            date_time__month=month,
            status='upcoming'
        ).values_list('date_time', 'duration')
        room_booked_ranges = [
            (dt.replace(tzinfo=None) if dt.tzinfo else dt,
             (dt.replace(tzinfo=None) if dt.tzinfo else dt) + datetime.timedelta(minutes=d))
            for dt, d in room_booked
        ]

    DAY_MAP = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'}

    dates = []
    for day_num in range(1, days_in_month + 1):
        date = datetime.date(year, month, day_num)
        day_abbr = DAY_MAP[date.weekday()]

        # Check if working day
        is_working = (
            day_abbr in working_hours and
            date not in leave_dates
        )

        if not is_working:
            dates.append({
                'date':             str(date),
                'is_working_day':   False,
                'has_availability': False,
                'slots':            [],
            })
            continue

        # Build slots based on working hours
        wh_start, wh_end = working_hours[day_abbr]
        slot_start = datetime.datetime.combine(date, wh_start)
        slot_end   = datetime.datetime.combine(date, wh_end)

        slots = []
        current = slot_start
        while current + dur_delta <= slot_end:
            # Skip past slots for today
            if date == today and current <= now:
                current += dur_delta
                continue

            slot_end_time = current + dur_delta

            # Check staff conflict
            staff_conflict = any(
                not (slot_end_time <= bs or current >= be)
                for bs, be in staff_booked_ranges
            )

            # Check room conflict
            room_conflict = False
            if room:
                room_conflict = any(
                    not (slot_end_time <= bs or current >= be)
                    for bs, be in room_booked_ranges
                )

            status = 'booked' if (staff_conflict or room_conflict) else 'available'
            slots.append({
                'time':   current.strftime('%H:%M'),
                'status': status,
            })
            current += dur_delta

        has_availability = any(s['status'] == 'available' for s in slots)

        dates.append({
            'date':             str(date),
            'is_working_day':   True,
            'has_availability': has_availability,
            'slots':            slots,
        })

    return dates


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
        from django.db.models import Q
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room_fk', 'price_plan'
        ).all()

        user = request.user
        if hasattr(user, 'role') and user.role == 'therapist':
            qs = qs.filter(staff=user)

        today     = request.query_params.get('today')
        date      = request.query_params.get('date')
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
            qs = qs.filter(
                Q(patient__name__icontains=search) |
                Q(treatment__name__icontains=search)
            )

        return Response(AppointmentSerializer(qs.distinct(), many=True).data)

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
                'patient', 'staff', 'treatment', 'room_fk', 'price_plan'
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
    ?staff_id=3&service_id=7&month=2026-05&room_id=1(optional)

    Returns full month availability with slots per day.
    Checks: staff working hours, staff leaves, existing appointments, room availability.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from treatments.models import Treatment
        from rooms.models import Room

        staff_id   = request.query_params.get('staff_id')
        service_id = request.query_params.get('service_id')
        month      = request.query_params.get('month')
        room_id    = request.query_params.get('room_id')

        if not staff_id or not service_id or not month:
            return Response({'error': 'staff_id, service_id and month are required.'}, status=400)

        # Validate month format
        try:
            year, mon = map(int, month.split('-'))
            if not (1 <= mon <= 12):
                raise ValueError
        except Exception:
            return Response({'error': 'Invalid month format. Use YYYY-MM.'}, status=400)

        try:
            staff = User.objects.get(id=staff_id, role__in=['therapist', 'reception'])
        except User.DoesNotExist:
            return Response({'error': 'Staff not found.'}, status=404)

        try:
            treatment = Treatment.objects.get(id=service_id)
        except Treatment.DoesNotExist:
            return Response({'error': 'Service not found.'}, status=404)

        room = None
        if room_id:
            try:
                room = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                return Response({'error': 'Room not found.'}, status=404)

        dates = _build_month_availability(staff, treatment, month, room)

        return Response({
            'month':                    month,
            'staff_id':                 int(staff_id),
            'service_id':               int(service_id),
            'service_duration_minutes': treatment.duration,
            'dates':                    dates,
        })


class AppointmentMetaView(APIView):
    """
    GET /api/appointments/meta/
    Returns all dropdown options with IDs for the booking form.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'statuses': [
                {'id': 1, 'value': 'upcoming',  'label': 'Upcoming'},
                {'id': 2, 'value': 'completed', 'label': 'Completed'},
                {'id': 3, 'value': 'cancelled', 'label': 'Cancelled'},
                {'id': 4, 'value': 'no_show',   'label': 'No Show'},
            ],
            'payment_statuses': [
                {'id': 1, 'value': 'pending',  'label': 'Pending'},
                {'id': 2, 'value': 'paid',     'label': 'Paid'},
                {'id': 3, 'value': 'refunded', 'label': 'Refunded'},
            ],
            'payment_types': [
                {'id': 1, 'value': 'single',  'label': 'Single'},
                {'id': 2, 'value': 'package', 'label': 'Package'},
            ],
            'consent_statuses': [
                {'id': 1, 'value': 'pending', 'label': 'Pending'},
                {'id': 2, 'value': 'signed',  'label': 'Signed'},
            ],
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
            'patient', 'staff', 'treatment', 'room_fk'
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
            'patient', 'staff', 'treatment', 'room_fk'
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