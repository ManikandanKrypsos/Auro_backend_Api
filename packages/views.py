from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminOrReception
from django.db.models import Q
from django.utils import timezone
import datetime

from .models import PatientPackage
from .serializers import (
    _package_full, _package_summary, _build_sessions,
    STATUS_MAP, PAY_TYPE_MAP, PAY_STATUS_MAP,
)


class PackageListView(APIView):
    """
    GET  /api/packages/         — list all packages
         ?patient_id=4          filter by patient
         ?treatment_id=7        filter by treatment
         ?status=active         filter by status
         ?search=name/phone     search patient

    POST /api/packages/         — create a new package
    Body:
    {
        "patient_id":       4,
        "treatment_id":     7,
        "price_plan_id":    3,
        "total_sessions":   5,
        "payment_amount":   "450.00",
        "payment_type_id":  2,
        "payment_status_id": 2,
        "notes":            "Paid upfront"
    }
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        qs = PatientPackage.objects.select_related(
            'patient', 'treatment', 'price_plan'
        ).all()

        patient_id   = request.query_params.get('patient_id')
        treatment_id = request.query_params.get('treatment_id')
        status       = request.query_params.get('status')
        search       = request.query_params.get('search', '').strip()

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if treatment_id:
            qs = qs.filter(treatment_id=treatment_id)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(patient__name__icontains=search) |
                Q(patient__phone__icontains=search)
            )

        return Response([_package_full(pkg) for pkg in qs])

    def post(self, request):
        from patients.models import Patient
        from treatments.models import Treatment, PricePlan

        patient_id      = request.data.get('patient_id')
        treatment_id    = request.data.get('treatment_id')
        price_plan_id   = request.data.get('price_plan_id')
        total_sessions  = request.data.get('total_sessions')
        payment_amount  = request.data.get('payment_amount')
        payment_type_id = request.data.get('payment_type_id', 2)
        pay_status_id   = request.data.get('payment_status_id', 1)
        notes           = request.data.get('notes', '')

        # Validate required fields
        if not all([patient_id, treatment_id, price_plan_id, total_sessions, payment_amount]):
            return Response({
                'error': 'patient_id, treatment_id, price_plan_id, total_sessions and payment_amount are required.'
            }, status=400)

        try:
            patient   = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found.'}, status=404)

        try:
            treatment = Treatment.objects.get(id=treatment_id)
        except Treatment.DoesNotExist:
            return Response({'error': 'Treatment not found.'}, status=404)

        try:
            plan = PricePlan.objects.get(id=price_plan_id, treatment=treatment)
        except PricePlan.DoesNotExist:
            return Response({'error': 'Price plan not found for this treatment.'}, status=404)

        pkg = PatientPackage.objects.create(
            patient=patient,
            treatment=treatment,
            price_plan=plan,
            total_sessions=int(total_sessions),
            payment_amount=payment_amount,
            payment_type=PAY_TYPE_MAP.get(int(payment_type_id), 'cash'),
            payment_status=PAY_STATUS_MAP.get(int(pay_status_id), 'pending'),
            notes=notes,
        )

        return Response(_package_full(pkg), status=201)


class PackageDetailView(APIView):
    """
    GET   /api/packages/<id>/          — package detail with full session timeline
    PATCH /api/packages/<id>/          — update package fields
    """
    permission_classes = [IsAdminOrReception]

    def _get(self, pk):
        try:
            return PatientPackage.objects.select_related(
                'patient', 'treatment', 'price_plan'
            ).get(pk=pk)
        except PatientPackage.DoesNotExist:
            return None

    def get(self, request, pk):
        pkg = self._get(pk)
        if not pkg:
            return Response({'error': 'Package not found.'}, status=404)
        return Response(_package_full(pkg, include_sessions=True))

    def patch(self, request, pk):
        pkg = self._get(pk)
        if not pkg:
            return Response({'error': 'Package not found.'}, status=404)

        if 'notes' in request.data:
            pkg.notes = request.data['notes']
        if 'payment_status_id' in request.data:
            pkg.payment_status = PAY_STATUS_MAP.get(int(request.data['payment_status_id']), pkg.payment_status)
        if 'payment_type_id' in request.data:
            pkg.payment_type = PAY_TYPE_MAP.get(int(request.data['payment_type_id']), pkg.payment_type)
        if 'payment_amount' in request.data:
            pkg.payment_amount = request.data['payment_amount']

        pkg.save()
        return Response(_package_full(pkg))


class PackageStatusView(APIView):
    """
    PATCH /api/packages/<id>/status/
    Body: { "status_id": 3 }
    status_id: 1=active, 2=completed, 3=cancelled
    """
    permission_classes = [IsAdminOrReception]

    def patch(self, request, pk):
        try:
            pkg = PatientPackage.objects.get(pk=pk)
        except PatientPackage.DoesNotExist:
            return Response({'error': 'Package not found.'}, status=404)

        status_id = request.data.get('status_id')
        if not status_id or int(status_id) not in STATUS_MAP:
            return Response({'error': 'Invalid status_id. Use 1=active, 2=completed, 3=cancelled.'}, status=400)

        pkg.status = STATUS_MAP[int(status_id)]
        pkg.save()

        return Response({
            'id':         pkg.id,
            'status':     pkg.status,
            'status_id':  pkg.status_id,
            'updated_at': pkg.updated_at,
        })


class PackageScheduleSessionView(APIView):
    """
    POST /api/packages/<id>/schedule-session/
    Schedule the next unscheduled session for a package.

    Body:
    {
        "staff_id": 2,
        "room_id":  1,
        "date":     "2026-05-20",
        "time":     "11:00",
        "notes":    "Optional"
    }
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request, pk):
        from appointments.models import Appointment
        from users.models import User
        from rooms.models import Room
        from appointments.serializers import AppointmentSerializer

        try:
            pkg = PatientPackage.objects.select_related(
                'patient', 'treatment', 'price_plan'
            ).get(pk=pk)
        except PatientPackage.DoesNotExist:
            return Response({'error': 'Package not found.'}, status=404)

        if pkg.status != 'active':
            return Response({'error': f'Package is {pkg.status}. Cannot schedule sessions.'}, status=400)

        if pkg.sessions_remaining == 0:
            return Response({'error': 'All sessions are already scheduled or completed.'}, status=400)

        staff_id = request.data.get('staff_id')
        room_id  = request.data.get('room_id')
        date_str = request.data.get('date')
        time_str = request.data.get('time')
        notes    = request.data.get('notes', '')

        if not all([staff_id, room_id, date_str, time_str]):
            return Response({'error': 'staff_id, room_id, date and time are required.'}, status=400)

        try:
            staff = User.objects.get(id=staff_id, role__in=['therapist', 'reception'])
        except User.DoesNotExist:
            return Response({'error': 'Staff not found.'}, status=404)

        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found.'}, status=404)

        # Auto-calculate next session number
        existing_count = Appointment.objects.filter(package=pkg).count()
        next_session_number = existing_count + 1

        if next_session_number > pkg.total_sessions:
            return Response({'error': 'All sessions already scheduled.'}, status=400)

        # Parse date + time
        import datetime as dt
        from django.utils import timezone as tz
        parts = time_str.strip().split('-')[0].strip().split(':')
        hour   = parts[0].zfill(2)
        minute = parts[1].strip() if len(parts) > 1 else '00'
        parsed_time = dt.datetime.strptime(f"{hour}:{minute}", '%H:%M').time()
        date_obj    = dt.date.fromisoformat(date_str)

        if date_obj < dt.date.today():
            return Response({'error': 'Cannot schedule session on a past date.'}, status=400)

        date_time = tz.make_aware(dt.datetime.combine(date_obj, parsed_time))

        # Create appointment linked to package
        appt = Appointment.objects.create(
            patient=pkg.patient,
            staff=staff,
            treatment=pkg.treatment,
            room_fk=room,
            price_plan=pkg.price_plan,
            package=pkg,
            date_time=date_time,
            duration=pkg.treatment.duration,
            session_number=next_session_number,
            total_sessions=pkg.total_sessions,
            status='upcoming',
            payment_status='pending',
            consent_status='pending',
            payment_type='cash',
            notes=notes,
        )

        return Response({
            'appointment': AppointmentSerializer(appt).data,
            'package':     _package_summary(pkg),
        }, status=201)


class PatientPackagesView(APIView):
    """
    GET /api/patients/<id>/packages/
    All packages for a specific patient.
    ?status=active|completed|cancelled
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from patients.models import Patient
        from appointments.models import Appointment
        from django.utils import timezone as tz

        # Support both DB id and patient_id string
        try:
            if str(pk).isdigit():
                patient = Patient.objects.get(id=int(pk))
            else:
                patient = Patient.objects.get(patient_id__iexact=pk)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found.'}, status=404)

        qs = PatientPackage.objects.filter(patient=patient).select_related(
            'treatment', 'price_plan'
        )

        status = request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        result = []
        for pkg in qs:
            # Next upcoming session
            next_appt = Appointment.objects.filter(
                package=pkg,
                status='upcoming'
            ).order_by('date_time').first()

            next_session = None
            if next_appt:
                dt = tz.localtime(next_appt.date_time) if next_appt.date_time and tz.is_aware(next_appt.date_time) else next_appt.date_time
                next_session = {
                    'appointment_id': next_appt.id,
                    'session_number': next_appt.session_number,
                    'date':           str(dt.date()) if dt else None,
                    'time':           dt.strftime('%H:%M') if dt else None,
                }

            result.append({
                'id':                 pkg.id,
                'treatment_detail': {
                    'id':       pkg.treatment.id,
                    'name':     pkg.treatment.name,
                    'duration': pkg.treatment.duration,
                    'category': pkg.treatment.category,
                },
                'price_plan_detail': {
                    'id':       pkg.price_plan.id,
                    'sessions': pkg.price_plan.sessions,
                    'price':    str(pkg.price_plan.price),
                },
                'total_sessions':     pkg.total_sessions,
                'sessions_completed': pkg.sessions_completed,
                'sessions_remaining': pkg.sessions_remaining,
                'status':             pkg.status,
                'status_id':          pkg.status_id,
                'payment_amount':     str(pkg.payment_amount),
                'payment_status':     pkg.payment_status,
                'payment_status_id':  pkg.payment_status_id,
                'next_session':       next_session,
                'created_at':         pkg.created_at,
            })

        return Response(result)