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
    Build full month availability. Every call reads fresh from DB — no caching.
    Priority order:
    1. Past dates                → is_working_day: false
    2. Clinic explicitly closed  → is_working_day: false
    3. Planned clinic holiday    → is_working_day: false
    4. Staff not scheduled       → is_working_day: false
    5. Staff on leave            → is_working_day: false
    6. Generate slots using tighter of clinic+staff hours
       - Break times → booked
       - Existing appointments (staff/room) → booked
       - Otherwise → available
    """
    import calendar
    from django.utils import timezone as dj_tz
    from users.models import StaffWorkingHours, StaffLeave, StaffBreakTime
    from clinic.models import ClinicHours, PlannedClosure

    duration  = treatment.duration
    dur_delta = datetime.timedelta(minutes=duration)
    today     = datetime.date.today()

    now_local = datetime.datetime.now()

    year, month = map(int, month_str.split('-'))
    _, days_in_month = calendar.monthrange(year, month)

    # ── Clinic hours — read fresh every call ──────────────────────────────────
    clinic_hours = {}
    for ch in ClinicHours.objects.all():
        if ch.is_open and ch.open_time and ch.close_time:
            clinic_hours[ch.day] = (ch.open_time, ch.close_time)
        else:
            clinic_hours[ch.day] = 'closed'

    # ── Planned holidays ──────────────────────────────────────────────────────
    clinic_closure_dates = set()
    for pc in PlannedClosure.objects.all():
        d = pc.from_date
        while d <= pc.to_date:
            clinic_closure_dates.add(d)
            d += datetime.timedelta(days=1)

    # ── Staff working hours ───────────────────────────────────────────────────
    staff_working_hours = {
        wh.day: (wh.start_time, wh.end_time)
        for wh in StaffWorkingHours.objects.filter(staff=staff)
    }

    # ── Staff leaves ──────────────────────────────────────────────────────────
    staff_leave_dates = set()
    for leave in StaffLeave.objects.filter(staff=staff):
        d = leave.from_date
        while d <= leave.to_date:
            staff_leave_dates.add(d)
            d += datetime.timedelta(days=1)

    # ── Staff breaks ──────────────────────────────────────────────────────────
    staff_break_ranges = [
        (bt.start_time, bt.end_time)
        for bt in StaffBreakTime.objects.filter(staff=staff)
    ]

    # ── Booked appointments — convert to local naive for comparison ───────────
    def to_local_naive(dt):
        if dt.tzinfo:
            try:
                return dj_tz.localtime(dt).replace(tzinfo=None)
            except Exception:
                return dt.replace(tzinfo=None)
        return dt

    staff_booked_ranges = []
    for appt_dt, appt_dur in Appointment.objects.filter(
        staff=staff,
        date_time__year=year,
        date_time__month=month,
        status='upcoming'
    ).values_list('date_time', 'duration'):
        s = to_local_naive(appt_dt)
        staff_booked_ranges.append((s, s + datetime.timedelta(minutes=max(appt_dur, duration))))

    room_booked_ranges = []
    if room:
        for appt_dt, appt_dur in Appointment.objects.filter(
            room_fk=room,
            date_time__year=year,
            date_time__month=month,
            status='upcoming'
        ).values_list('date_time', 'duration'):
            s = to_local_naive(appt_dt)
            room_booked_ranges.append((s, s + datetime.timedelta(minutes=max(appt_dur, duration))))

    DAY_MAP = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'}

    dates = []
    for day_num in range(1, days_in_month + 1):
        date     = datetime.date(year, month, day_num)
        day_abbr = DAY_MAP[date.weekday()]

        def closed():
            dates.append({'date': str(date), 'is_working_day': False,
                          'has_availability': False, 'slots': []})

        # 1. Past
        if date < today:
            closed(); continue

        # 2. Clinic closed (explicitly set to closed)
        clinic_val = clinic_hours.get(day_abbr)
        if clinic_val == 'closed':
            closed(); continue

        # 3. Holiday
        if date in clinic_closure_dates:
            closed(); continue

        # 4. Staff not working
        if day_abbr not in staff_working_hours:
            closed(); continue

        # 5. Staff on leave
        if date in staff_leave_dates:
            closed(); continue

        # Effective hours
        staff_open, staff_close = staff_working_hours[day_abbr]
        if clinic_val and clinic_val != 'closed':
            clinic_open, clinic_close = clinic_val
            effective_open  = max(clinic_open,  staff_open)
            effective_close = min(clinic_close, staff_close)
        else:
            # Clinic hours not configured → use staff hours only
            effective_open  = staff_open
            effective_close = staff_close

        slot_start = datetime.datetime.combine(date, effective_open)
        slot_end   = datetime.datetime.combine(date, effective_close)

        slots   = []
        current = slot_start
        while current + dur_delta <= slot_end:
            if date == today and current <= now_local:
                current += dur_delta
                continue

            slot_end_time = current + dur_delta

            staff_conflict = any(
                not (slot_end_time <= bs or current >= be)
                for bs, be in staff_booked_ranges
            )
            room_conflict = room and any(
                not (slot_end_time <= bs or current >= be)
                for bs, be in room_booked_ranges
            )
            break_conflict = any(
                not (slot_end_time.time() <= bs or current.time() >= be)
                for bs, be in staff_break_ranges
            )

            status = 'booked' if (staff_conflict or room_conflict or break_conflict) else 'available'
            slots.append({
                'time':   f"{current.strftime('%H:%M')} - {slot_end_time.strftime('%H:%M')}",
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


def _update_patient_category(patient):
    """Auto-update patient category based on completed treatment count."""
    if not patient:
        return
    if patient.category == 'VIP':
        return
    completed_count = Appointment.objects.filter(
        patient=patient,
        status='completed'
    ).values('treatment').distinct().count()
    if completed_count > 1:
        patient.category = 'Returning'
        patient.save()


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
        return [IsAuthenticated()]

    def get(self, request):
        from django.db.models import Q
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room_fk', 'price_plan'
        ).all()

        # Filter by role — fetch fresh from DB to ensure role is loaded
        from users.models import User as UserModel
        try:
            current_user = UserModel.objects.get(pk=request.user.pk)
            user_role    = current_user.role or ''
        except Exception:
            user_role = ''

        if user_role == 'therapist':
            qs = qs.filter(staff_id=request.user.pk)

        today      = request.query_params.get('today')
        date       = request.query_params.get('date')
        date_from  = request.query_params.get('date_from')
        date_to    = request.query_params.get('date_to')
        staff_id   = request.query_params.get('staff_id')
        status     = request.query_params.get('status')
        consent    = request.query_params.get('consent_status')
        payment_st = request.query_params.get('payment_status')
        search     = request.query_params.get('search', '').strip()

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
        if consent:
            qs = qs.filter(consent_status=consent)
        if payment_st:
            qs = qs.filter(payment_status=payment_st)
        package_id = request.query_params.get('package_id')
        if package_id:
            qs = qs.filter(package_id=package_id)
        if search:
            qs = qs.filter(
                Q(patient__name__icontains=search) |
                Q(treatment__name__icontains=search)
            )

        return Response(AppointmentSerializer(qs.distinct(), many=True).data)

    def post(self, request):
        serializer = AppointmentWriteSerializer(data=request.data)
        if serializer.is_valid():
            data      = serializer.validated_data
            staff     = data.get('staff')
            treatment = data.get('treatment')
            duration  = data.get('duration') or (treatment.duration if treatment else 60)

            # Build date_time from request data (date + time fields)
            import datetime
            req_date = request.data.get('date')
            req_time = request.data.get('time', '')
            # time may be "16:00" or "16:00-17:15" — take only start time
            req_time_start = req_time.split('-')[0].strip() if req_time else None
            date_time = None
            if req_date and req_time_start:
                try:
                    date_time = datetime.datetime.strptime(
                        f"{req_date} {req_time_start}", '%Y-%m-%d %H:%M'
                    )
                except Exception:
                    pass

            # ── Clinic closing time check ─────────────────────────────────────
            if date_time and duration:
                from clinic.models import ClinicHours
                day_name = date_time.strftime('%a')
                clinic_hours = ClinicHours.objects.filter(day=day_name).first()
                if clinic_hours and clinic_hours.is_open and clinic_hours.close_time:
                    slot_end_time = (date_time + datetime.timedelta(minutes=duration)).time()
                    if slot_end_time > clinic_hours.close_time:
                        return Response({
                            'error': f"This appointment cannot be booked. The session ends at "
                                     f"{slot_end_time.strftime('%H:%M')} but the clinic closes at "
                                     f"{clinic_hours.close_time.strftime('%H:%M')} on {day_name}. "
                                     f"Please choose an earlier time slot."
                        }, status=400)
            # ─────────────────────────────────────────────────────────────────

            # ── Double booking check ──────────────────────────────────────────
            if staff and date_time:
                slot_end = date_time + datetime.timedelta(minutes=duration)
                conflict = Appointment.objects.filter(
                    staff=staff,
                    status__in=['upcoming', 'in_session'],
                )
                overlapping = [
                    a for a in conflict
                    if a.date_time.replace(tzinfo=None) < slot_end and
                       (a.date_time + datetime.timedelta(minutes=a.duration)).replace(tzinfo=None) > date_time
                ]
                if overlapping:
                    existing = overlapping[0]
                    return Response({
                        'error': f"This time slot is already booked for {staff.username}. "
                                 f"They have an appointment at {existing.date_time.strftime('%H:%M')}. "
                                 f"Please choose a different time or therapist."
                    }, status=400)
            # ─────────────────────────────────────────────────────────────────

            appt = serializer.save()
            try:
                from .tasks import send_booking_confirmation
                send_booking_confirmation.delay(appt.id)
            except Exception:
                pass
            _update_patient_category(appt.patient)

            # Auto-create pending ConsentRecord when appointment is booked
            try:
                from patients.models import ConsentRecord
                ConsentRecord.objects.get_or_create(
                    patient=appt.patient,
                    appointment=appt,
                    defaults={
                        'title':            f"Consent — {appt.treatment.name if appt.treatment else 'Treatment'}",
                        'file_name':        '',
                        'file_url':         '',
                        'status':           'pending',
                        'patient_signed':   False,
                        'therapist_signed': False,
                    }
                )
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
    Body: { "status": "in_session" }
    Status options: upcoming | in_session | completed | cancelled
    Any authenticated user can update status.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            appt = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found.'}, status=404)

        status = request.data.get('status')
        valid  = ['upcoming', 'in_session', 'completed', 'cancelled']
        if status not in valid:
            return Response({'error': f'Status must be one of: {valid}'}, status=400)

        appt.status = status
        appt.save()

        # Auto-update patient category
        if status == 'completed':
            _update_patient_category(appt.patient)

        # Remove pending consent record when appointment is cancelled
        if status == 'cancelled':
            try:
                from patients.models import ConsentRecord
                ConsentRecord.objects.filter(
                    patient=appt.patient,
                    appointment=appt,
                    status='pending'
                ).delete()
            except Exception:
                pass

        # Auto-update package if linked
        package_detail = None
        if appt.package_id and status == 'completed':
            pkg = appt.package
            pkg.sessions_completed = pkg.appointments.filter(status='completed').count()
            if pkg.sessions_completed >= pkg.total_sessions:
                pkg.status = 'completed'
            pkg.save()
            package_detail = {
                'id':                  pkg.id,
                'sessions_completed':  pkg.sessions_completed,
                'sessions_remaining':  pkg.sessions_remaining,
                'status':              pkg.status,
                'status_id':           pkg.status_id,
            }

        data = AppointmentSerializer(appt).data
        data['package_detail'] = package_detail
        return Response(data)


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
    Send as multipart/form-data to upload PDF from phone.

    Fields:
    - consent_status: signed | pending
    - consent_file:   PDF file upload from phone (multipart)
    - consent_form_url: URL string (if not uploading file)
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

        # Handle PDF file upload from phone
        consent_file = request.FILES.get('consent_file')
        if consent_file:
            import os, time
            from django.conf import settings
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'consent_forms')
            os.makedirs(upload_dir, exist_ok=True)
            ext      = os.path.splitext(consent_file.name)[1].lower() or '.pdf'
            filename = f"consent_{appt.id}_{int(time.time())}{ext}"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb+') as f:
                for chunk in consent_file.chunks():
                    f.write(chunk)
            base_url = request.build_absolute_uri('/')
            appt.consent_form_url = f"{base_url.rstrip('/')}{settings.MEDIA_URL}consent_forms/{filename}"
        elif url:
            appt.consent_form_url = url

        appt.save()

        # Auto-create a ConsentRecord on the patient so it shows in patient consent tab
        if appt.consent_status == 'signed' and appt.consent_form_url:
            from patients.models import ConsentRecord
            ConsentRecord.objects.get_or_create(
                patient=appt.patient,
                file_url=appt.consent_form_url,
                defaults={
                    'title':            f"Consent — {appt.treatment.name if appt.treatment else 'Treatment'}",
                    'file_name':        f"consent_{appt.id}.pdf",
                    'status':           'signed',
                    'patient_signed':   True,
                    'therapist_signed': False,
                    'signed_date':      appt.date_time.date() if appt.date_time else None,
                }
            )

        return Response({
            'message':          'Consent updated.',
            'consent_status':   appt.consent_status,
            'consent_form_url': appt.consent_form_url,
        })


class AvailableSlotsView(APIView):
    """
    GET /api/appointments/available-slots/
    ?staff_id=20&service_id=58&month=2026-05&room_id=14(optional)

    Returns full month with effective_window and blocked_ranges per day.
    No slots array — frontend calculates slots from effective_window minus blocked_ranges.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from treatments.models import Treatment
        from rooms.models import Room
        from users.models import StaffWorkingHours, StaffLeave, StaffBreakTime
        from clinic.models import ClinicHours, PlannedClosure
        import calendar as cal_module
        from django.utils import timezone as dj_tz

        staff_id   = request.query_params.get('staff_id')
        service_id = request.query_params.get('service_id')
        month      = request.query_params.get('month')
        room_id    = request.query_params.get('room_id')

        if not staff_id or not service_id or not month:
            return Response({'error': 'staff_id, service_id and month are required.'}, status=400)

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

        today = datetime.date.today()
        now_local = datetime.datetime.now()
        _, days_in_month = cal_module.monthrange(year, mon)
        DAY_MAP = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'}

        # Clinic hours
        clinic_hours = {}
        for ch in ClinicHours.objects.all():
            if ch.is_open and ch.open_time and ch.close_time:
                clinic_hours[ch.day] = (ch.open_time, ch.close_time)
            else:
                clinic_hours[ch.day] = 'closed'

        # Clinic holidays
        clinic_closure_dates = set()
        for pc in PlannedClosure.objects.all():
            d = pc.from_date
            while d <= pc.to_date:
                clinic_closure_dates.add(d)
                d += datetime.timedelta(days=1)

        # Staff working hours
        staff_working_hours = {
            wh.day: (wh.start_time, wh.end_time)
            for wh in StaffWorkingHours.objects.filter(staff=staff)
        }

        # Staff leaves
        staff_leave_dates = set()
        for leave in StaffLeave.objects.filter(staff=staff):
            d = leave.from_date
            while d <= leave.to_date:
                staff_leave_dates.add(d)
                d += datetime.timedelta(days=1)

        # Staff breaks
        staff_breaks = list(StaffBreakTime.objects.filter(staff=staff))

        # Booked appointments for staff this month
        staff_appts = Appointment.objects.filter(
            staff=staff,
            date_time__year=year,
            date_time__month=mon,
            status='upcoming'
        ).select_related('patient', 'treatment')

        # Booked appointments for room this month
        room_appts = []
        if room:
            room_appts = list(Appointment.objects.filter(
                room_fk=room,
                date_time__year=year,
                date_time__month=mon,
                status='upcoming'
            ).select_related('patient', 'treatment'))

        def to_local_naive(dt):
            if dt.tzinfo:
                try:
                    return dj_tz.localtime(dt).replace(tzinfo=None)
                except Exception:
                    return dt.replace(tzinfo=None)
            return dt

        def fmt_time(t):
            return t.strftime('%H:%M') if hasattr(t, 'strftime') else str(t)[:5]

        dates = []
        for day_num in range(1, days_in_month + 1):
            date     = datetime.date(year, mon, day_num)
            day_abbr = DAY_MAP[date.weekday()]

            def closed_day():
                dates.append({
                    'date':             str(date),
                    'is_working_day':   False,
                    'effective_window': None,
                    'blocked_ranges':   [],
                })

            # Past dates
            if date < today:
                closed_day(); continue

            # Clinic closed
            clinic_val = clinic_hours.get(day_abbr)
            if clinic_val == 'closed':
                closed_day(); continue

            # Holiday
            if date in clinic_closure_dates:
                closed_day(); continue

            # Staff not working
            if day_abbr not in staff_working_hours:
                closed_day(); continue

            # Staff on leave
            if date in staff_leave_dates:
                closed_day(); continue

            # Effective window = tighter of clinic + staff hours
            staff_open, staff_close = staff_working_hours[day_abbr]
            if clinic_val and clinic_val != 'closed':
                clinic_open, clinic_close = clinic_val
                eff_open  = max(clinic_open,  staff_open)
                eff_close = min(clinic_close, staff_close)
            else:
                eff_open  = staff_open
                eff_close = staff_close

            blocked = []

            # Break times
            for bt in staff_breaks:
                blocked.append({
                    'start': fmt_time(bt.start_time),
                    'end':   fmt_time(bt.end_time),
                    'type':  'break',
                    'label': bt.label if bt.label else 'Staff Break',
                })

            # Booked staff appointments
            for a in staff_appts:
                appt_dt = to_local_naive(a.date_time)
                if appt_dt.date() != date:
                    continue
                appt_end     = appt_dt + datetime.timedelta(minutes=a.duration or treatment.duration)
                patient_name = a.patient.name if a.patient else 'Patient'
                treat_name   = a.treatment.name if a.treatment else 'Appointment'

                # Same treatment → booked, different treatment → therapist_occupied
                if a.treatment_id == treatment.id:
                    blocked.append({
                        'start':          appt_dt.strftime('%H:%M'),
                        'end':            appt_end.strftime('%H:%M'),
                        'type':           'booked',
                        'label':          f"{patient_name} — {treat_name}",
                        'appointment_id': a.id,
                    })
                else:
                    blocked.append({
                        'start':          appt_dt.strftime('%H:%M'),
                        'end':            appt_end.strftime('%H:%M'),
                        'type':           'therapist_occupied',
                        'label':          'Therapist Occupied',
                        'appointment_id': a.id,
                    })

            # Room booked appointments
            for a in room_appts:
                appt_dt = to_local_naive(a.date_time)
                if appt_dt.date() != date:
                    continue
                appt_end = appt_dt + datetime.timedelta(minutes=a.duration or treatment.duration)
                # Skip if already in staff blocked (same appointment)
                if any(b.get('appointment_id') == a.id for b in blocked):
                    continue
                blocked.append({
                    'start': appt_dt.strftime('%H:%M'),
                    'end':   appt_end.strftime('%H:%M'),
                    'type':  'room_occupied',
                    'label': 'Room Occupied',
                })

            # Sort blocked by start time
            blocked.sort(key=lambda x: x['start'])

            dates.append({
                'date':           str(date),
                'is_working_day': True,
                'effective_window': {
                    'start': fmt_time(eff_open),
                    'end':   fmt_time(eff_close),
                },
                'blocked_ranges': blocked,
            })

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
                {'id': 1, 'value': 'upcoming',   'label': 'Upcoming'},
                {'id': 2, 'value': 'in_session', 'label': 'In Session'},
                {'id': 3, 'value': 'completed',  'label': 'Completed'},
                {'id': 4, 'value': 'cancelled',  'label': 'Cancelled'},
            ],
            'payment_statuses': [
                {'id': 1, 'value': 'pending',  'label': 'Pending'},
                {'id': 2, 'value': 'paid',     'label': 'Paid'},
                {'id': 3, 'value': 'refunded', 'label': 'Refunded'},
            ],
            'payment_types': [
                {'id': 1, 'value': 'online', 'label': 'Online Payment'},
                {'id': 2, 'value': 'cash',   'label': 'Cash'},
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
    ?date=2026-04-30                           single day
    ?start_date=2026-05-01&end_date=2026-05-31 date range

    Returns appointments grouped by date within the range.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room_fk'
        ).exclude(status='cancelled')

        if hasattr(request.user, 'role') and request.user.role == 'therapist':
            qs = qs.filter(staff=request.user)

        # Optional staff_id filter
        staff_id = request.query_params.get('staff_id')
        if staff_id:
            qs = qs.filter(staff__id=staff_id)

        # Optional room_id filter
        room_id = request.query_params.get('room_id')
        if room_id:
            qs = qs.filter(room_fk__id=room_id)

        # Optional service_id filter
        service_id = request.query_params.get('service_id')
        if service_id:
            qs = qs.filter(treatment__id=service_id)

        date       = request.query_params.get('date')
        start_date = request.query_params.get('start_date')
        end_date   = request.query_params.get('end_date')

        # Single day
        if date:
            parsed = parse_date(date)
            if not parsed:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
            qs = qs.filter(date_time__date=parsed)
            return Response({
                'start_date':   str(parsed),
                'end_date':     str(parsed),
                'total':        qs.count(),
                'appointments': AppointmentSerializer(qs.order_by('date_time'), many=True).data,
            })

        # Date range
        if start_date and end_date:
            parsed_start = parse_date(start_date)
            parsed_end   = parse_date(end_date)
            if not parsed_start or not parsed_end:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
            if parsed_start > parsed_end:
                return Response({'error': 'start_date must be before end_date.'}, status=400)

            qs = qs.filter(
                date_time__date__gte=parsed_start,
                date_time__date__lte=parsed_end
            ).order_by('date_time')

            # Group by date
            grouped = {}
            for appt in qs:
                day = str(appt.date_time.date())
                if day not in grouped:
                    grouped[day] = []
                grouped[day].append(AppointmentSerializer(appt).data)

            # Fill all days in range even if no appointments
            result = []
            current = parsed_start
            while current <= parsed_end:
                day_str = str(current)
                result.append({
                    'date':         day_str,
                    'total':        len(grouped.get(day_str, [])),
                    'appointments': grouped.get(day_str, []),
                })
                current += datetime.timedelta(days=1)

            return Response({
                'start_date': str(parsed_start),
                'end_date':   str(parsed_end),
                'total':      qs.count(),
                'days':       result,
            })

        return Response({'error': 'Provide date or start_date and end_date params.'}, status=400)