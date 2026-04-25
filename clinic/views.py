from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin
from .models import ClinicHours, PlannedClosure
from .serializers import (
    ClinicHoursSerializer, BulkClinicHoursSerializer, PlannedClosureSerializer
)

DAYS_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _init_clinic_hours():
    """Create default closed entries for all 7 days if they don't exist."""
    for day in DAYS_ORDER:
        ClinicHours.objects.get_or_create(day=day, defaults={'is_open': False})


class ClinicHoursView(APIView):
    """
    GET  /api/clinic/hours/   — get all 7 days schedule
    POST /api/clinic/hours/   — save all 7 days at once (bulk)

    POST body (send all 7 days):
    [
        { "day": "Mon", "is_open": true,  "open_time": "09:00", "close_time": "18:00" },
        { "day": "Tue", "is_open": true,  "open_time": "09:00", "close_time": "18:00" },
        { "day": "Wed", "is_open": true,  "open_time": "09:00", "close_time": "18:00" },
        { "day": "Thu", "is_open": true,  "open_time": "09:00", "close_time": "18:00" },
        { "day": "Fri", "is_open": true,  "open_time": "09:00", "close_time": "18:00" },
        { "day": "Sat", "is_open": false },
        { "day": "Sun", "is_open": false }
    ]
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        _init_clinic_hours()
        hours = {h.day: h for h in ClinicHours.objects.all()}
        result = []
        for day in DAYS_ORDER:
            h = hours.get(day)
            result.append({
                'id':         h.id if h else None,
                'day':        day,
                'is_open':    h.is_open if h else False,
                'open_time':  h.open_time if h else None,
                'close_time': h.close_time if h else None,
            })
        return Response(result)

    def post(self, request):
        data = request.data
        if not isinstance(data, list):
            return Response({'error': 'Send a list of all 7 days.'}, status=400)

        errors  = {}
        results = []

        for item in data:
            serializer = BulkClinicHoursSerializer(data=item)
            if not serializer.is_valid():
                errors[item.get('day', 'unknown')] = serializer.errors
                continue

            v   = serializer.validated_data
            day = v['day']

            obj, _ = ClinicHours.objects.get_or_create(day=day)
            obj.is_open    = v.get('is_open', False)
            obj.open_time  = v.get('open_time')  if obj.is_open else None
            obj.close_time = v.get('close_time') if obj.is_open else None
            obj.save()
            results.append(ClinicHoursSerializer(obj).data)

        if errors:
            return Response({'errors': errors, 'saved': results}, status=400)
        return Response(results)


class ClinicHoursDayView(APIView):
    """
    PATCH /api/clinic/hours/<day>/   — update a single day
    e.g. PATCH /api/clinic/hours/Mon/

    Body:
    { "is_open": true, "open_time": "09:00", "close_time": "18:00" }
    or
    { "is_open": false }
    """
    permission_classes = [IsAdmin]

    def patch(self, request, day):
        if day not in DAYS_ORDER:
            return Response({'error': f'Invalid day. Use: {", ".join(DAYS_ORDER)}'}, status=400)

        obj, _ = ClinicHours.objects.get_or_create(day=day)
        serializer = ClinicHoursSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            # Clear times if closed
            if not instance.is_open:
                instance.open_time  = None
                instance.close_time = None
                instance.save()
            return Response(ClinicHoursSerializer(instance).data)
        return Response(serializer.errors, status=400)

    def put(self, request, day):
        return self.patch(request, day)


# ── Planned Closures ──────────────────────────────────────────────────────────

class PlannedClosureListView(APIView):
    """
    GET  /api/clinic/closures/   — list all planned closures
    POST /api/clinic/closures/   — add a planned closure

    POST body:
    {
        "from_date": "2026-05-01",
        "to_date":   "2026-05-03",
        "reason":    "National Holiday"
    }
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        closures = PlannedClosure.objects.all()
        return Response(PlannedClosureSerializer(closures, many=True).data)

    def post(self, request):
        serializer = PlannedClosureSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class PlannedClosureDetailView(APIView):
    """
    GET    /api/clinic/closures/<id>/   — get single closure
    PATCH  /api/clinic/closures/<id>/   — edit closure
    DELETE /api/clinic/closures/<id>/   — delete closure
    """
    permission_classes = [IsAdmin]

    def _get(self, pk):
        try:
            return PlannedClosure.objects.get(pk=pk)
        except PlannedClosure.DoesNotExist:
            return None

    def get(self, request, pk):
        closure = self._get(pk)
        if not closure:
            return Response({'error': 'Closure not found.'}, status=404)
        return Response(PlannedClosureSerializer(closure).data)

    def patch(self, request, pk):
        closure = self._get(pk)
        if not closure:
            return Response({'error': 'Closure not found.'}, status=404)
        serializer = PlannedClosureSerializer(closure, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        closure = self._get(pk)
        if not closure:
            return Response({'error': 'Closure not found.'}, status=404)
        closure.delete()
        return Response({'message': 'Closure deleted successfully.'})