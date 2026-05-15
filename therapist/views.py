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

        # Current session — status is in_session
        current = appts.filter(
            status='in_session'
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
        ).filter(staff=therapist).exclude(status='cancelled').order_by('date_time')

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


# ── Therapist Product Usage ───────────────────────────────────────────────────

class TherapistProductUsageView(APIView):
    """
    POST /api/therapist/products/use/
    Therapist logs products used in a session.
    Automatically deducts from inventory.

    Body:
    {
        "products": [
            { "inventory_id": 3, "quantity": 2 },
            { "inventory_id": 7, "quantity": 1 }
        ],
        "notes": "Used during facial session"
    }

    GET /api/therapist/products/use/
    ?filter=today | week | all (default: all)
    Returns product usage history for this therapist.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from inventory.models import StockMovement
        from django.utils import timezone
        import datetime

        try:
            therapist = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        filter_by = request.query_params.get('filter', 'all')
        now  = timezone.now()
        today = timezone.localdate()

        qs = StockMovement.objects.filter(
            type='out'
        ).select_related('item').order_by('-created_at')

        if filter_by == 'today':
            qs = qs.filter(created_at__date=today)
        elif filter_by == 'week':
            week_start = now - datetime.timedelta(days=7)
            qs = qs.filter(created_at__gte=week_start)

        result = []
        # Group by appointment if available
        grouped = {}
        for movement in qs:
            appt_id = movement.appointment_id if hasattr(movement, 'appointment_id') else None
            key = appt_id or f"no_appt_{movement.id}"
            if key not in grouped:
                grouped[key] = {
                    'appointment_id': appt_id,
                    'date':           str(movement.created_at.date()),
                    'products':       [],
                }
            grouped[key]['products'].append({
                'id':           movement.id,
                'inventory_id': movement.item.id,
                'product_name': movement.item.name,
                'unit':         movement.item.unit,
                'quantity':     movement.quantity,
                'notes':        movement.note,
                'created_at':   movement.created_at,
            })

        return Response(list(grouped.values()))

    def patch(self, request, movement_id):
        """
        PATCH /api/therapist/products/use/<movement_id>/
        Edit quantity or inventory item of a logged product usage.
        Body: { "quantity": 3 } or { "inventory_id": 5 } or both
        """
        from inventory.models import InventoryItem, StockMovement

        try:
            therapist = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        try:
            movement = StockMovement.objects.select_related('item').get(id=movement_id, type='out')
        except StockMovement.DoesNotExist:
            return Response({'error': 'Product usage record not found.'}, status=404)

        new_quantity     = request.data.get('quantity')
        new_inventory_id = request.data.get('inventory_id')

        old_item     = movement.item
        old_quantity = movement.quantity

        # Handle inventory item change
        if new_inventory_id and int(new_inventory_id) != old_item.id:
            try:
                new_item = InventoryItem.objects.get(id=new_inventory_id)
            except InventoryItem.DoesNotExist:
                return Response({'error': 'Inventory item not found.'}, status=404)
            # Restore old item stock
            old_item.current_stock += old_quantity
            old_item.save()
            # Deduct from new item
            qty = int(new_quantity) if new_quantity else old_quantity
            if new_item.current_stock < qty:
                return Response({'error': f'Insufficient stock for {new_item.name}. Available: {new_item.current_stock}'}, status=400)
            new_item.current_stock -= qty
            new_item.save()
            movement.item     = new_item
            movement.quantity = qty
        elif new_quantity and int(new_quantity) != old_quantity:
            # Only quantity changed
            diff = int(new_quantity) - old_quantity
            if diff > 0 and old_item.current_stock < diff:
                return Response({'error': f'Insufficient stock. Available: {old_item.current_stock}'}, status=400)
            old_item.current_stock -= diff
            old_item.save()
            movement.quantity = int(new_quantity)

        if 'notes' in request.data:
            movement.note = request.data['notes']

        movement.save()

        return Response({
            'message':         'Product usage updated.',
            'movement_id':     movement.id,
            'inventory_id':    movement.item.id,
            'product_name':    movement.item.name,
            'unit':            movement.item.unit,
            'quantity':        movement.quantity,
            'stock_remaining': movement.item.current_stock,
        })

    def post(self, request):
        from inventory.models import InventoryItem, StockMovement

        try:
            therapist = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        products = request.data.get('products', [])
        notes    = request.data.get('notes', '')

        if not products:
            return Response({'error': 'products list is required.'}, status=400)

        errors   = []
        movements = []

        for item in products:
            inventory_id = item.get('inventory_id')
            quantity     = item.get('quantity', 0)

            if not inventory_id or quantity <= 0:
                errors.append(f"Invalid product entry: {item}")
                continue

            try:
                inv_item = InventoryItem.objects.get(id=inventory_id)
            except InventoryItem.DoesNotExist:
                errors.append(f"Inventory item {inventory_id} not found.")
                continue

            if inv_item.current_stock < quantity:
                errors.append(
                    f"Insufficient stock for '{inv_item.name}'. "
                    f"Available: {inv_item.current_stock}, Requested: {quantity}"
                )
                continue

            # Deduct from inventory
            inv_item.current_stock -= quantity
            inv_item.save()

            # Log stock movement
            movement = StockMovement.objects.create(
                item=inv_item,
                type='out',
                quantity=quantity,
                note=notes or f"Used in session by {therapist.username or therapist.email}",
            )
            movements.append({
                'inventory_id':  inv_item.id,
                'product_name':  inv_item.name,
                'unit':          inv_item.unit,
                'quantity_used': quantity,
                'stock_remaining': inv_item.current_stock,
                'movement_id':   movement.id,
            })

        if errors and not movements:
            return Response({'errors': errors}, status=400)

        return Response({
            'message':       'Products logged and inventory updated.',
            'products_used': movements,
            'errors':        errors if errors else None,
        }, status=201)