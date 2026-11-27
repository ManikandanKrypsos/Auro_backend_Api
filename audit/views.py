"""
Audit trail (admin only, read only).

GET /api/audit/            newest first, always paginated (?page=1&page_size=50, max 100)
    ?category=clinical,financial,stock   ?action=patient_updated,refund_issued
    ?patient_id=Aura12   ?actor_id=   ?target_type=patient|appointment|session_note|document|invoice|payment|inventory_item
    ?target_id=   ?date_from=YYYY-MM-DD ?date_to=   ?search= (target, patient, actor or summary text)
GET /api/audit/actions/    categories + every action with its label (for filters)
"""
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.metrics import day_start
from users.permissions import IsAdmin
from utils.api_errors import validation_error
from .models import AuditEvent
from .recorder import ACTIONS, label

CATEGORIES = dict(AuditEvent.CATEGORY_CHOICES)


def serialize(e):
    return {
        'id': e.id,
        'category': e.category, 'category_label': CATEGORIES.get(e.category, e.category),
        'action': e.action, 'action_label': label(e.action), 'summary': e.summary,
        'actor_id': e.actor_id, 'actor_name': e.actor_label or 'System', 'actor_role': e.actor_role or None,
        'target_type': e.target_type, 'target_id': e.target_id, 'target_label': e.target_label,
        'patient_id': e.patient.patient_id if e.patient_id and e.patient else None,
        'patient_name': e.patient_label or None,
        'changed_fields': e.changed_fields or [],
        'before': e.before, 'after': e.after,
        'request_id': e.request_id or None,
        'source': e.source,
        'created_at': e.created_at.isoformat(),
    }


class AuditListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from patients.models import Patient
        from utils.pagination import paginate
        p, errors = request.query_params, {}
        qs = AuditEvent.objects.select_related('patient')
        for f in ('category', 'action', 'target_type'):
            if p.get(f):
                qs = qs.filter(**{f'{f}__in': [x.strip() for x in p[f].split(',') if x.strip()]})
        if p.get('target_id'):
            qs = qs.filter(target_id=p['target_id'].strip())
        if p.get('actor_id'):
            if not str(p['actor_id']).isdigit():
                errors['actor_id'] = 'Must be a whole number.'
            else:
                qs = qs.filter(actor_id=int(p['actor_id']))
        if p.get('patient_id'):
            v = p['patient_id'].strip()
            patient = Patient.objects.filter(patient_id__iexact=v).first() or \
                (Patient.objects.filter(pk=int(v)).first() if v.isdigit() else None)
            qs = qs.filter(patient=patient) if patient else qs.none()
        for f, op in (('date_from', 'gte'), ('date_to', 'lt')):
            if p.get(f):
                d = parse_date(p[f])
                if not d:
                    errors[f] = 'Use YYYY-MM-DD.'
                    continue
                import datetime
                qs = qs.filter(**{f'created_at__{op}': day_start(d if op == 'gte' else d + datetime.timedelta(days=1))})
        if p.get('search'):
            s = p['search'].strip()
            qs = qs.filter(Q(target_label__icontains=s) | Q(patient_label__icontains=s) | Q(actor_label__icontains=s)
                           | Q(summary__icontains=s) | Q(target_id__iexact=s))
        if errors:
            return validation_error(errors)
        if 'page' not in p and 'page_size' not in p:          # always paginated: this table only grows
            request._request.GET = request._request.GET.copy()
            request._request.GET['page_size'] = '50'
        return paginate(request, qs.order_by('-created_at', '-id'), lambda rows: [serialize(e) for e in rows])


class AuditActionsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            'categories': [{'value': k, 'label': v} for k, v in CATEGORIES.items()],
            'actions': [{'value': a, 'label': l, 'category': c} for a, (c, l) in ACTIONS.items()],
        })
