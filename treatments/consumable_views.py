"""
Consumables per treatment, and what an appointment used.

GET    /api/treatments/<id>/consumables/              list + cost / margin   (any staff)
POST   /api/treatments/<id>/consumables/              {item_id, quantity}     (admin)
PUT    /api/treatments/<id>/consumables/              {items: [{item_id, quantity}]}  replace all (admin)
PATCH  /api/treatments/<id>/consumables/<link_id>/    {quantity}              (admin)
DELETE /api/treatments/<id>/consumables/<link_id>/                            (admin)
GET    /api/appointments/<id>/consumption/            confirmed usage or pre-fill (any staff; therapist: own)
POST   /api/appointments/<id>/consumption/            therapist confirms actual usage → deducts stock
GET    /api/appointments/consumption/pending/         completed sessions with usage not confirmed yet
GET    /api/appointments/consumption/review/          confirmed usage waiting for admin review (admin)
POST   /api/appointments/<id>/consumption/review/     admin marks the confirmed usage reviewed {note?}
"""
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin, IsAdminOrReadOnly, IsClinicStaff
from utils.api_errors import error, validation_error
from .models import Treatment, TreatmentConsumable


def _f(v):
    return round(float(v or 0), 2)


def serialize_link(c):
    cost = float(c.item.cost_per_unit or 0)
    return {
        'id': c.id, 'item_id': c.item_id, 'item_name': c.item.name, 'sku': c.item.sku, 'unit': c.item.unit,
        'quantity': c.quantity, 'unit_cost': _f(cost), 'cost': _f(cost * c.quantity),
        'current_stock': c.item.current_stock,
        'enough_for': c.item.current_stock // c.quantity if c.quantity else None,   # how many more treatments
    }


def consumables_payload(treatment):
    links = [serialize_link(c) for c in TreatmentConsumable.objects.filter(treatment=treatment).select_related('item')]
    cost = _f(sum(l['cost'] for l in links))
    price = _f(treatment.price) if treatment.price is not None else None
    return {
        'treatment_id': treatment.id,
        'consumables': links,
        'consumables_cost': cost,
        'price': price,
        'margin': _f(price - cost) if price is not None else None,
        'margin_pct': round((price - cost) / price * 100, 1) if price else None,
    }


def _qty(value, errors, field='quantity'):
    raw = str(value if value is not None else '').strip()
    if not raw.isdigit() or not 1 <= int(raw) <= 9999:
        errors[field] = 'Whole number from 1 to 9999.'
        return None
    return int(raw)


def _item(value, errors, field='item_id'):
    from inventory.models import InventoryItem
    raw = str(value if value is not None else '').strip()
    item = InventoryItem.objects.filter(pk=int(raw)).first() if raw.isdigit() else None
    if item is None:
        errors[field] = 'Inventory item not found.'
    return item


class TreatmentConsumablesView(APIView):
    def get_permissions(self):
        return [IsAdmin()] if self.request.method in ('POST', 'PUT') else [IsAdminOrReadOnly()]

    def _treatment(self, pk):
        return Treatment.objects.filter(pk=pk).first()

    def get(self, request, pk):
        t = self._treatment(pk)
        if not t:
            return error(404, 'treatment_not_found', 'Treatment not found.')
        return Response(consumables_payload(t))

    def post(self, request, pk):
        t = self._treatment(pk)
        if not t:
            return error(404, 'treatment_not_found', 'Treatment not found.')
        errors = {}
        item = _item(request.data.get('item_id'), errors)
        qty = _qty(request.data.get('quantity', 1), errors)
        if errors:
            return validation_error(errors)
        if TreatmentConsumable.objects.filter(treatment=t, item=item).exists():
            return error(409, 'already_linked', f'{item.name} is already on this treatment — change its quantity instead.')
        TreatmentConsumable.objects.create(treatment=t, item=item, quantity=qty)
        return Response(consumables_payload(t), status=201)

    def put(self, request, pk):
        t = self._treatment(pk)
        if not t:
            return error(404, 'treatment_not_found', 'Treatment not found.')
        items = request.data.get('items')
        if not isinstance(items, list):
            return validation_error({'items': 'Send a list of {item_id, quantity} (an empty list removes all).'})
        errors, wanted = {}, {}
        for n, it in enumerate(items):
            if not isinstance(it, dict):
                errors[f'items[{n}]'] = 'Each entry must be an object.'
                continue
            item = _item(it.get('item_id'), errors, f'items[{n}].item_id')
            qty = _qty(it.get('quantity', 1), errors, f'items[{n}].quantity')
            if item and item.id in wanted:
                errors[f'items[{n}].item_id'] = 'Listed twice.'
            elif item and qty:
                wanted[item.id] = qty
        if errors:
            return validation_error(errors)
        with transaction.atomic():
            TreatmentConsumable.objects.filter(treatment=t).exclude(item_id__in=wanted).delete()
            for item_id, qty in wanted.items():
                TreatmentConsumable.objects.update_or_create(treatment=t, item_id=item_id, defaults={'quantity': qty})
        return Response(consumables_payload(t))


class TreatmentConsumableDetailView(APIView):
    permission_classes = [IsAdmin]

    def _link(self, pk, link_id):
        return TreatmentConsumable.objects.select_related('treatment', 'item').filter(pk=link_id, treatment_id=pk).first()

    def patch(self, request, pk, link_id):
        c = self._link(pk, link_id)
        if not c:
            return error(404, 'consumable_not_found', 'This item is not on the treatment.')
        errors = {}
        qty = _qty(request.data.get('quantity'), errors)
        if errors:
            return validation_error(errors)
        c.quantity = qty
        c.save(update_fields=['quantity', 'updated_at'])
        return Response(consumables_payload(c.treatment))

    def delete(self, request, pk, link_id):
        c = self._link(pk, link_id)
        if not c:
            return error(404, 'consumable_not_found', 'This item is not on the treatment.')
        t = c.treatment
        c.delete()
        return Response(consumables_payload(t))


def _own_appointment(request, pk):
    from appointments.models import Appointment
    appt = Appointment.objects.select_related('treatment', 'patient', 'staff').filter(pk=pk).first()
    if not appt or (getattr(request.user, 'role', '') == 'therapist' and appt.staff_id != request.user.pk):
        return None
    return appt


def _usage_response(appt, status=200):
    from .consumption import summary
    data = summary(appt)
    data.update({'appointment_id': appt.id, 'status': appt.status,
                 'treatment': appt.treatment.name if appt.treatment_id and appt.treatment else None})
    return Response(data, status=status)


class AppointmentConsumptionView(APIView):
    """
    GET  — confirmed usage, or the pre-fill from the treatment's consumables (any staff; therapist: own)
    POST — confirm what was actually used. The only thing that takes consumables out of stock.
           {"items": [{"item_id": 34, "quantity": 2, "lot_id": 7, "type": "used"}], "note": "..."}
           type: used (default) | waste (broken / wasted — deducted as wastage) | returned (brought back
           unused — recorded, stock untouched). The same item may appear once per type.
           Sending it again replaces the earlier confirmation (stock is put back, then re-deducted).
           "items": [] confirms that nothing was used.
    """
    permission_classes = [IsClinicStaff]

    def get(self, request, pk):
        appt = _own_appointment(request, pk)
        if not appt:
            return error(404, 'appointment_not_found', 'Appointment not found.')
        return _usage_response(appt)

    def post(self, request, pk):
        from inventory.models import Lot
        from .consumption import CONFIRMABLE, TYPES, confirm_usage
        appt = _own_appointment(request, pk)
        if not appt:
            return error(404, 'appointment_not_found', 'Appointment not found.')
        if appt.status not in CONFIRMABLE:
            return error(400, 'not_in_session', 'Usage can only be confirmed for an appointment that is in session or completed.')
        items = request.data.get('items')
        if not isinstance(items, list):
            return validation_error({'items': 'Send a list of {item_id, quantity, lot_id?, type?} (an empty list = nothing used).'})
        errors, lines, seen = {}, [], set()
        for n, it in enumerate(items):
            if not isinstance(it, dict):
                errors[f'items[{n}]'] = 'Each entry must be an object.'
                continue
            item = _item(it.get('item_id'), errors, f'items[{n}].item_id')
            raw = str(it.get('quantity') if it.get('quantity') is not None else '').strip()
            if not raw.isdigit() or int(raw) > 9999:
                errors[f'items[{n}].quantity'] = 'Whole number from 0 to 9999.'
                continue
            qty = int(raw)
            kind = str(it.get('type') or 'used').strip().lower()
            if kind not in TYPES:
                errors[f'items[{n}].type'] = 'Use "used", "waste" or "returned".'
                continue
            if item and (item.id, kind) in seen:
                errors[f'items[{n}].item_id'] = f'Listed twice as "{kind}".'
                continue
            lot = None
            if it.get('lot_id') not in (None, '') and item:
                lot = Lot.objects.filter(pk=int(it['lot_id']), item=item).first() if str(it['lot_id']).isdigit() else None
                if lot is None:
                    errors[f'items[{n}].lot_id'] = 'Lot not found for this item.'
            if item and qty > 0:
                seen.add((item.id, kind))
                lines.append((item, qty, lot, kind))
        if errors:
            return validation_error(errors)
        confirm_usage(appt, lines, request.user, str(request.data.get('note') or ''))
        return _usage_response(appt, 201)


class PendingConsumptionView(APIView):
    """
    GET /api/appointments/consumption/pending/  — completed appointments whose treatment has consumables
    but whose usage was never confirmed (stock not deducted yet). Therapists: their own.
    ?staff_id= ?date_from= ?date_to=   ·   opt-in pagination ?page= &page_size=
    """
    permission_classes = [IsClinicStaff]

    def get(self, request):
        from django.utils.dateparse import parse_date
        from appointments.models import Appointment
        from utils.pagination import paginate
        qs = (Appointment.objects.filter(status='completed', treatment__consumables__isnull=False)
              .exclude(consumption_records__reversed=False)
              .select_related('patient', 'staff', 'treatment').distinct().order_by('-date_time'))
        p = request.query_params
        if getattr(request.user, 'role', '') == 'therapist':
            qs = qs.filter(staff=request.user)
        elif p.get('staff_id'):
            if not str(p['staff_id']).isdigit():
                return validation_error({'staff_id': 'Must be a whole number.'})
            qs = qs.filter(staff_id=int(p['staff_id']))
        for field, lookup in (('date_from', 'date_time__date__gte'), ('date_to', 'date_time__date__lte')):
            if p.get(field):
                d = parse_date(p[field])
                if not d:
                    return validation_error({field: 'Use YYYY-MM-DD.'})
                qs = qs.filter(**{lookup: d})

        def row(a):
            return {'appointment_id': a.id, 'date_time': a.date_time.isoformat(),
                    'patient_id': a.patient.patient_id if a.patient else None,
                    'patient_name': a.patient.name if a.patient else None,
                    'staff_id': a.staff_id, 'staff_name': (a.staff.username or a.staff.email.split('@')[0]) if a.staff else None,
                    'treatment_id': a.treatment_id, 'treatment': a.treatment.name if a.treatment else None}
        return paginate(request, qs, lambda objs: [row(a) for a in objs])


def _staff_date_filters(request, qs, staff_field, date_field):
    """?staff_id= ?date_from= ?date_to= (appointment date). Returns (qs, error_response)."""
    from django.utils.dateparse import parse_date
    p = request.query_params
    if p.get('staff_id'):
        if not str(p['staff_id']).isdigit():
            return None, validation_error({'staff_id': 'Must be a whole number.'})
        qs = qs.filter(**{staff_field: int(p['staff_id'])})
    for field, op in (('date_from', 'gte'), ('date_to', 'lte')):
        if p.get(field):
            d = parse_date(p[field])
            if not d:
                return None, validation_error({field: 'Use YYYY-MM-DD.'})
            qs = qs.filter(**{f'{date_field}__date__{op}': d})
    return qs, None


def _review_row(rec):
    from .consumption import _name
    a = rec.appointment
    lines = list(rec.lines.all())
    return {
        'appointment_id': a.id, 'record_id': rec.id, 'date_time': a.date_time.isoformat(), 'status': a.status,
        'patient_id': a.patient.patient_id if a.patient else None,
        'patient_name': a.patient.name if a.patient else None,
        'staff_id': a.staff_id, 'staff_name': _name(a.staff),
        'treatment_id': a.treatment_id, 'treatment': a.treatment.name if a.treatment else None,
        'confirmed_by': _name(rec.confirmed_by), 'confirmed_at': rec.created_at.isoformat(), 'note': rec.note,
        'item_count': len(lines),
        'total_cost': round(sum(float(l.unit_cost) * l.quantity for l in lines if l.type != 'returned'), 2),
        'has_shortfall': any(l.shortfall for l in lines),
        'has_waste': any(l.type == 'waste' for l in lines),
        'has_returned': any(l.type == 'returned' for l in lines),
        'differs_from_recipe': any((l.type == 'used' and l.quantity != l.planned) or l.type != 'used' for l in lines),
        'reviewed': rec.reviewed, 'reviewed_by': _name(rec.reviewed_by) if rec.reviewed else None,
        'reviewed_at': rec.reviewed_at.isoformat() if rec.reviewed_at else None, 'review_note': rec.review_note,
    }


class ConsumptionReviewListView(APIView):
    """
    GET /api/appointments/consumption/review/   (admin)
    Confirmed session usage, newest first. ?status=pending (default, not reviewed yet) | reviewed | all
    ?staff_id= ?date_from= ?date_to= (appointment date) · opt-in pagination ?page= &page_size=
    Only the current confirmation of each appointment is listed (edits replace it).
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        from django.db.models import Prefetch
        from utils.pagination import paginate
        from .models import AppointmentConsumption, SessionConsumption
        qs = (SessionConsumption.objects.filter(reversed=False)
              .select_related('appointment', 'appointment__patient', 'appointment__staff',
                              'appointment__treatment', 'confirmed_by', 'reviewed_by')
              .prefetch_related(Prefetch('lines', queryset=AppointmentConsumption._base_manager.all()))
              .order_by('-created_at'))
        status = request.query_params.get('status', 'pending')
        if status not in ('pending', 'reviewed', 'all'):
            return validation_error({'status': 'Use pending, reviewed or all.'})
        if status != 'all':
            qs = qs.filter(reviewed=(status == 'reviewed'))
        qs, bad = _staff_date_filters(request, qs, 'appointment__staff_id', 'appointment__date_time')
        if bad:
            return bad
        return paginate(request, qs, lambda objs: [_review_row(r) for r in objs])


class ConsumptionReviewView(APIView):
    """
    POST /api/appointments/<id>/consumption/review/   (admin)   {"note": "Checked against the vial log"}
    Marks the appointment's current confirmed usage as reviewed. Sending it again updates the note.
    If the therapist later edits the usage, the new confirmation is unreviewed again.
    """
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from .consumption import active_record, review
        appt = _own_appointment(request, pk)
        if not appt:
            return error(404, 'appointment_not_found', 'Appointment not found.')
        rec = active_record(appt)
        if not rec:
            return error(400, 'not_confirmed', 'The therapist has not confirmed the product usage for this appointment yet.')
        note = request.data.get('note') or ''
        if not isinstance(note, str) or len(note) > 500:
            return validation_error({'note': 'Text of at most 500 characters.'})
        review(rec, request.user, note.strip())
        return _usage_response(appt)
