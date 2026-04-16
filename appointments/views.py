from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.utils import timezone
from collections import defaultdict
import datetime

from users.permissions import IsAdminOrReception
from .models import Appointment
from .serializers import AppointmentSerializer
from .tasks import (
    send_booking_confirmation,
    send_reminder_24h,
    send_reminder_2h,
    send_post_treatment_followup,
    send_rebooking_reminder,
)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['patient__name', 'status', 'room']

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.all().order_by('date_time')

        if user.role == 'therapist':
            qs = qs.filter(staff=user)

        date      = self.request.query_params.get('date')
        date_from = self.request.query_params.get('date_from')
        date_to   = self.request.query_params.get('date_to')
        staff_id  = self.request.query_params.get('staff')
        room      = self.request.query_params.get('room')
        status    = self.request.query_params.get('status')

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
        if room:
            qs = qs.filter(room__icontains=room)
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrReception()]
        return [IsAuthenticated()]

def perform_create(self, serializer):
    appt = serializer.save()
    appt_time = appt.date_time

    try:
        send_booking_confirmation.delay(appt.id)
        send_reminder_24h.apply_async(
            args=[appt.id],
            eta=appt_time - datetime.timedelta(hours=24)
        )
        send_reminder_2h.apply_async(
            args=[appt.id],
            eta=appt_time - datetime.timedelta(hours=2)
        )
        send_post_treatment_followup.apply_async(
            args=[appt.id],
            eta=appt_time + datetime.timedelta(days=3)
        )
        send_rebooking_reminder.apply_async(
            args=[appt.id],
            eta=appt_time + datetime.timedelta(days=30)
        )
    except Exception as e:
        # Don't crash if Redis/Celery not available
        print(f"Celery task error: {e}")

    @action(detail=False, methods=['get'], url_path='today')   # 👈 indented inside class
    def today(self, request):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end   = today_start + datetime.timedelta(days=1)
        qs = self.get_queryset().filter(
            date_time__gte=today_start,
            date_time__lt=today_end
        )
        return Response(AppointmentSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='week')    # 👈 indented inside class
    def week(self, request):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_end    = today_start + datetime.timedelta(days=7)
        qs = self.get_queryset().filter(
            date_time__gte=today_start,
            date_time__lt=week_end
        )
        return Response(AppointmentSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='by-room')
    def by_room(self, request):
        date = request.query_params.get('date')
        qs = self.get_queryset()
        if date:
            parsed = parse_date(date)
            if parsed:
                qs = qs.filter(date_time__date=parsed)
        grouped = defaultdict(list)
        for appt in qs:
            grouped[appt.room].append(AppointmentSerializer(appt).data)
        return Response(grouped)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        appt = self.get_object()
        new_status = request.data.get('status')
        valid = [s[0] for s in Appointment.STATUS_CHOICES]
        if new_status not in valid:
            return Response({'error': f'Status must be one of: {valid}'}, status=400)
        appt.status = new_status
        appt.save()
        return Response(AppointmentSerializer(appt).data)