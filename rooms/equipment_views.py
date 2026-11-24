"""
Equipment — the clinic's physical machines (bookable resources).

GET    /api/equipment/            list (?search= ?status=active|maintenance|retired ?room_id=)   any staff
POST   /api/equipment/            {name, model?, serial_number?, room_id?, status?, notes?}     admin + reception
GET    /api/equipment/<id>/       one machine + the treatments that need it                      any staff
PATCH  /api/equipment/<id>/       any of the fields above                                        admin + reception
DELETE /api/equipment/<id>/       treatments that needed it just stop requiring a machine        admin + reception
GET    /api/equipment/statuses/   status choices for dropdowns

A treatment that needs a machine has `equipment_id` (set on POST/PATCH /api/treatments/).
Booking / rescheduling returns 409 `equipment_double_booked` when another appointment uses the same
machine at an overlapping time, or `equipment_unavailable` when the machine is in maintenance / retired.
"""
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsStaffReadAdminOrReceptionWrite
from utils.api_errors import error, validation_error
from .models import Equipment, Room

STATUS_LABELS = dict(Equipment.STATUS_CHOICES)


def serialize(e, detail=False):
    out = {
        'id': e.id, 'name': e.name, 'model': e.model, 'serial_number': e.serial_number,
        'room_id': e.room_id, 'room_name': e.room.name if e.room_id and e.room else None,
        'status': e.status, 'status_label': STATUS_LABELS.get(e.status, e.status),
        'is_bookable': e.status == 'active',
        'notes': e.notes, 'created_at': e.created_at.isoformat(), 'updated_at': e.updated_at.isoformat(),
    }
    if detail:
        out['treatments'] = [{'id': t.id, 'name': t.name} for t in e.treatments.all().order_by('name')]
    return out


def _apply(e, data, partial):
    errors = {}
    if not partial or 'name' in data:
        name = str(data.get('name') or '').strip()
        if not name:
            errors['name'] = 'Name is required.'
        elif len(name) > 100:
            errors['name'] = 'At most 100 characters.'
        else:
            e.name = name
    for f in ('model', 'serial_number'):
        if f in data:
            v = str(data.get(f) or '').strip()
            if len(v) > 100:
                errors[f] = 'At most 100 characters.'
            else:
                setattr(e, f, v)
    if 'notes' in data:
        e.notes = str(data.get('notes') or '')
    if 'status' in data:
        if data['status'] not in STATUS_LABELS:
            errors['status'] = f'Use one of: {", ".join(STATUS_LABELS)}.'
        else:
            e.status = data['status']
    if 'room_id' in data:
        rid = data.get('room_id')
        if rid in (None, ''):
            e.room = None
        else:
            room = Room.objects.filter(pk=int(rid)).first() if str(rid).isdigit() else None
            if not room:
                errors['room_id'] = 'Room not found.'
            else:
                e.room = room
    if errors:
        return validation_error(errors)
    try:
        e.save()
    except IntegrityError:
        return error(409, 'duplicate_name', f'There is already a machine called "{e.name}".')
    return None


class EquipmentListView(APIView):
    permission_classes = [IsStaffReadAdminOrReceptionWrite]

    def get(self, request):
        qs = Equipment.objects.select_related('room')
        p = request.query_params
        if p.get('search'):
            from django.db.models import Q
            s = p['search'].strip()
            qs = qs.filter(Q(name__icontains=s) | Q(model__icontains=s) | Q(serial_number__icontains=s))
        if p.get('status'):
            qs = qs.filter(status__in=[x.strip() for x in p['status'].split(',') if x.strip()])
        if p.get('room_id') and str(p['room_id']).isdigit():
            qs = qs.filter(room_id=int(p['room_id']))
        return Response([serialize(e) for e in qs])

    def post(self, request):
        e = Equipment()
        bad = _apply(e, request.data, partial=False)
        if bad:
            return bad
        return Response(serialize(e, detail=True), status=201)


class EquipmentDetailView(APIView):
    permission_classes = [IsStaffReadAdminOrReceptionWrite]

    def _get(self, pk):
        return Equipment.objects.select_related('room').filter(pk=pk).first()

    def get(self, request, pk):
        e = self._get(pk)
        if not e:
            return error(404, 'equipment_not_found', 'Equipment not found.')
        return Response(serialize(e, detail=True))

    def patch(self, request, pk):
        e = self._get(pk)
        if not e:
            return error(404, 'equipment_not_found', 'Equipment not found.')
        bad = _apply(e, request.data, partial=True)
        if bad:
            return bad
        return Response(serialize(e, detail=True))

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        e = self._get(pk)
        if not e:
            return error(404, 'equipment_not_found', 'Equipment not found.')
        e.delete()
        return Response({'message': 'Equipment deleted.'})


class EquipmentStatusesView(APIView):
    permission_classes = [IsStaffReadAdminOrReceptionWrite]

    def get(self, request):
        return Response([{'value': k, 'label': v} for k, v in Equipment.STATUS_CHOICES])
