import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin, IsAdminOrReception
from .errors import error, lead_not_found, validation_error
from .models import Lead, LeadActivity, LeadTask
from .serializers import (
    LeadSerializer, LeadListSerializer, LeadWriteSerializer,
    LeadStageUpdateSerializer, LeadActivityWriteSerializer,
    STAGE_MAP, STAGE_ID_MAP, SOURCE_MAP, scheduled_phones_for, scheduled_patients_for,
)


def _list_context(items):
    return {'scheduled_phones': scheduled_phones_for(items), 'scheduled_patients': scheduled_patients_for(items)}


class LeadMetaView(APIView):
    """
    GET /api/leads/meta/  — all dropdown options with IDs
    """
    def get(self, request):
        return Response({
            'marketing_sources': [
                {'id': 1, 'value': 'instagram', 'label': 'Instagram'},
                {'id': 2, 'value': 'web',       'label': 'Website'},
                {'id': 3, 'value': 'walk_in',   'label': 'Walk-in'},
                {'id': 4, 'value': 'referral',  'label': 'Referral'},
                {'id': 5, 'value': 'whatsapp',  'label': 'WhatsApp'},
                {'id': 6, 'value': 'other',     'label': 'Other'},
            ],
            'stages': [
                {'id': 1, 'value': 'new_inquiries', 'label': 'New'},
                {'id': 2, 'value': 'engaged',       'label': 'Contacted'},
                {'id': 3, 'value': 'consultation',  'label': 'Consultation'},
                {'id': 5, 'value': 'converted',     'label': 'Won'},
                {'id': 6, 'value': 'lost',          'label': 'Lost'},
            ],
        })


ACTIVE_STAGES = ['new_inquiries', 'engaged', 'consultation']           # still open
ALL_STAGES    = ['new_inquiries', 'engaged', 'consultation', 'converted', 'lost']


def _trend(current, previous):
    """Percent change, same shape as the dashboard: {value, change_pct, trend}."""
    if previous == 0:
        pct   = 100.0 if current > 0 else 0.0
        trend = 'up' if current > 0 else 'neutral'
    else:
        pct   = round((current - previous) / previous * 100, 1)
        trend = 'up' if pct > 0 else ('down' if pct < 0 else 'neutral')
    return {'value': current, 'change_pct': abs(pct), 'trend': trend}


def _lead_snapshot(qs):
    total     = qs.count()
    active    = qs.filter(stage__in=ACTIVE_STAGES).count()
    converted = qs.filter(stage='converted').count()
    valuation = float(qs.aggregate(t=Sum('value'))['t'] or 0)
    rate      = round(converted / total * 100, 1) if total else 0.0
    return total, active, rate, valuation


class LeadStatsView(APIView):
    """
    GET /api/leads/stats/
    KPI tiles + per-stage count/valuation for the pipeline columns.

    Comparison ("vs. mes anterior") = the same numbers for leads that existed
    before the 1st of this month. Leads have no stage history, so for active /
    conversion / valuation the comparison uses each lead's current stage & value.
      total_leads, active, valuation → change_pct (percent change)
      conversion_rate                → change_pp  (percentage-point difference)
    conversion_rate = converted leads / total leads × 100
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        now            = timezone.localtime()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total, active, rate, valuation = _lead_snapshot(Lead.objects.all())
        p_total, p_active, p_rate, p_valuation = _lead_snapshot(
            Lead.objects.filter(created_at__lt=start_of_month)
        )

        change_pp = round(rate - p_rate, 1)
        stages = {
            s: {'count': 0, 'valuation': 0.0} for s in ALL_STAGES
        }
        for row in Lead.objects.values('stage').annotate(count=Count('id'), valuation=Sum('value')):
            if row['stage'] in stages:
                stages[row['stage']] = {
                    'count':     row['count'],
                    'valuation': float(row['valuation'] or 0),
                }

        return Response({
            'total_leads':     _trend(total, p_total),
            'active':          _trend(active, p_active),
            'conversion_rate': {
                'value_pct': rate,
                'change_pp': abs(change_pp),
                'trend':     'up' if change_pp > 0 else ('down' if change_pp < 0 else 'neutral'),
            },
            'valuation':       _trend(valuation, p_valuation),
            'stages':          stages,
            # Legacy flat counts kept for the current UI
            'new_inquiries': stages['new_inquiries']['count'],
            'engaged':       stages['engaged']['count'],
            'consultation':  stages['consultation']['count'],
            'lost':          stages['lost']['count'],
        })


class LeadPipelineView(APIView):
    """
    GET /api/leads/pipeline/
    Returns leads grouped by pipeline stage — used for the kanban board.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        pipeline_stages = [
            ('new_inquiries', 'New'),
            ('engaged',       'Contacted'),
            ('consultation',  'Consultation'),
            ('converted',     'Won'),
            ('lost',          'Lost'),
        ]
        result = []
        for stage, label in pipeline_stages:
            leads = Lead.objects.filter(stage=stage).select_related('assigned_to', 'converted_patient').order_by('-created_at')
            result.append({
                'stage':       stage,
                'stage_label': label,
                'count':       leads.count(),
                'stage_id':    STAGE_ID_MAP[stage],
                'leads':       LeadListSerializer(leads, many=True, context=_list_context(list(leads))).data,
            })
        return Response(result)


class LeadListView(APIView):
    """
    GET  /api/leads/           — list leads
         ?search=name/phone/email
         ?stage_id=2  (or 2,3)       1=New 2=Contacted 3=Consultation 5=Won 6=Lost (4 = Won, old id)
         ?stage=engaged              ?source=instagram
         ?service_id=7               ?marketing_source_id=3
         ?assigned_staff_id=4
         ?date_from=2026-11-01&date_to=2026-11-30   (by created date, inclusive)
         All filters optional and combinable.
         Pagination (opt-in): ?page=1&page_size=20 (max 100) → returns
         {count, page, page_size, total_pages, results}. Without page/page_size
         the response is a plain list, as before.
    POST /api/leads/           — create new inquiry
    """
    def get_permissions(self):
        return [IsAdminOrReception()]

    @staticmethod
    def _int_param(params, name, errors):
        raw = params.get(name, '').strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            errors[name] = 'Must be an integer.'
            return None

    @staticmethod
    def _date_param(params, name, errors):
        raw = params.get(name, '').strip()
        if not raw:
            return None
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            errors[name] = 'Use YYYY-MM-DD.'
            return None

    def get(self, request):
        params = request.query_params
        errors = {}
        leads  = Lead.objects.select_related('assigned_to', 'converted_patient').order_by('-created_at', '-id')
        search = params.get('search', '').strip()
        stage  = params.get('stage', '').strip()
        source = params.get('source', '').strip()

        service_id          = self._int_param(params, 'service_id', errors)
        marketing_source_id = self._int_param(params, 'marketing_source_id', errors)
        assigned_staff_id   = self._int_param(params, 'assigned_staff_id', errors)
        date_from           = self._date_param(params, 'date_from', errors)
        date_to             = self._date_param(params, 'date_to', errors)
        stage_keys = None
        raw_stage_ids = params.get('stage_id', '').strip()
        if raw_stage_ids:
            parts = [p.strip() for p in raw_stage_ids.split(',') if p.strip()]
            if not parts or any(not p.isdigit() or int(p) not in STAGE_MAP for p in parts):
                errors['stage_id'] = 'Use 1=New, 2=Contacted, 3=Consultation, 5=Won, 6=Lost (comma-separate for several).'
            else:
                stage_keys = {STAGE_MAP[int(p)] for p in parts}
        if marketing_source_id is not None and marketing_source_id not in SOURCE_MAP:
            errors['marketing_source_id'] = 'Use 1=Instagram, 2=Web, 3=Walk-In, 4=Referral, 5=WhatsApp, 6=Other.'
        if errors:
            return validation_error(errors)

        if search:
            leads = leads.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        if stage:
            leads = leads.filter(stage__in=[x.strip() for x in stage.split(',') if x.strip()])
        if stage_keys is not None:
            leads = leads.filter(stage__in=stage_keys)
        if source:
            leads = leads.filter(source=source)
        if service_id is not None:
            leads = leads.filter(service_id=service_id)
        if marketing_source_id is not None:
            leads = leads.filter(source=SOURCE_MAP[marketing_source_id])
        if assigned_staff_id is not None:
            leads = leads.filter(assigned_to_id=assigned_staff_id)
        if date_from:
            leads = leads.filter(created_at__gte=timezone.make_aware(
                datetime.datetime.combine(date_from, datetime.time.min)))
        if date_to:
            leads = leads.filter(created_at__lt=timezone.make_aware(
                datetime.datetime.combine(date_to + datetime.timedelta(days=1), datetime.time.min)))

        paginate = 'page' in params or 'page_size' in params
        if paginate:
            page_size = self._int_param(params, 'page_size', errors) or 20
            page_num  = self._int_param(params, 'page', errors) or 1
            if errors:
                return validation_error(errors)
            page_size = max(1, min(page_size, 100))
            paginator = Paginator(leads, page_size)
            page      = paginator.get_page(page_num)
            items     = list(page.object_list)
        else:
            items = list(leads)

        data = LeadListSerializer(items, many=True, context=_list_context(items)).data

        if paginate:
            return Response({
                'count':       paginator.count,
                'page':        page.number,
                'page_size':   page_size,
                'total_pages': paginator.num_pages,
                'results':     data,
            })
        return Response(data)

    def post(self, request):
        serializer = LeadWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error(serializer.errors)
        lead = serializer.save()
        log(lead, 'created', request.user, f'Lead created ({STAGE_LABELS.get(lead.stage, lead.stage)}).',
            {'stage_id': STAGE_ID_MAP.get(lead.stage)})
        if lead.assigned_to_id:
            log(lead, 'assigned', request.user, f'Assigned to {_name(lead.assigned_to)}.',
                {'from_staff_id': None, 'to_staff_id': lead.assigned_to_id})
            from notifications import service as notify
            notify.lead_assigned(lead, request.user)
        return Response(LeadSerializer(lead).data, status=201)


# ── Helpers ───────────────────────────────────────────────────────────────────

STAGE_LABELS = {'new_inquiries': 'New', 'engaged': 'Contacted', 'consultation': 'Consultation',
                'converted': 'Won', 'lost': 'Lost'}


def _name(user):
    if user is None:
        return 'nobody'
    return user.username or user.email.split('@')[0]


def log(lead, action, user, note='', data=None):
    return LeadActivity.objects.create(lead=lead, action=action, note=note, data=data or {}, created_by=user)


def _get_lead(pk):
    return (Lead.objects.select_related('assigned_to', 'converted_patient', 'converted_by')
            .filter(pk=pk).first())


def log_stage_change(lead, old_stage, user, note=''):
    if lead.stage == old_stage:
        return
    text = f"Stage: {old_stage} → {lead.stage}. {note}".strip()   # same text format as before
    log(lead, 'stage_change', user, text, {
        'from_stage_id': STAGE_ID_MAP.get(old_stage), 'to_stage_id': STAGE_ID_MAP.get(lead.stage),
        'from_stage': old_stage, 'to_stage': lead.stage, 'note': note or '',
    })


def log_assignment(lead, old_staff, user):
    if lead.assigned_to_id == (old_staff.id if old_staff else None):
        return
    text = (f'Assigned to {_name(lead.assigned_to)}.' if lead.assigned_to_id else 'Unassigned.')
    if old_staff is not None:
        text = f'Reassigned from {_name(old_staff)} to {_name(lead.assigned_to)}.' if lead.assigned_to_id \
            else f'Unassigned (was {_name(old_staff)}).'
    log(lead, 'assigned', user, text, {'from_staff_id': old_staff.id if old_staff else None,
                                       'to_staff_id': lead.assigned_to_id})


def _detail(lead):
    """Lead detail = list fields + conversion links + task counts."""
    data = LeadSerializer(lead).data
    appt = None
    if lead.converted_patient_id:
        from appointments.models import Appointment
        qs = Appointment.objects.filter(patient_id=lead.converted_patient_id).exclude(status='cancelled')
        if lead.converted_at:
            qs = qs.filter(created_at__gte=lead.converted_at) if hasattr(Appointment, 'created_at') else qs
        appt = qs.order_by('date_time', 'id').first()
    data['converted_appointment_id'] = appt.id if appt else None
    data['converted_by'] = ({'id': lead.converted_by_id, 'name': _name(lead.converted_by)}
                            if lead.converted_by_id else None)
    tasks = LeadTask.objects.filter(lead=lead)
    data['open_tasks_count'] = tasks.filter(is_done=False).count()
    nxt = tasks.filter(is_done=False, due_date__isnull=False).order_by('due_date', 'id').first()
    data['next_task'] = _task(nxt) if nxt else None
    return data


class LeadDetailView(APIView):
    """
    GET    /api/leads/<id>/      lead + converted_appointment_id, converted_by, open_tasks_count, next_task
    PATCH  /api/leads/<id>/      any create field; stage and assignment changes are logged to history
    DELETE /api/leads/<id>/
    """
    def get_permissions(self):
        return [IsAdminOrReception()]

    def get(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        return Response(_detail(lead))

    def patch(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        serializer = LeadWriteSerializer(lead, data=request.data, partial=True)
        if not serializer.is_valid():
            return validation_error(serializer.errors)
        old_stage, old_staff = lead.stage, lead.assigned_to
        lead = serializer.save()
        log_stage_change(lead, old_stage, request.user)
        log_assignment(lead, old_staff, request.user)
        if lead.assigned_to_id and lead.assigned_to_id != (old_staff.id if old_staff else None):
            from notifications import service as notify
            notify.lead_assigned(lead, request.user)
        return Response(_detail(_get_lead(lead.pk)))

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        lead.delete()
        return Response({'message': 'Lead deleted.'})


class LeadStageView(APIView):
    """
    PATCH /api/leads/<id>/stage/
    Move lead to a different pipeline stage.
    Body: { "stage_id": 2, "note": "Called and interested" }
    """
    permission_classes = [IsAdminOrReception]

    def patch(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        serializer = LeadStageUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error(serializer.errors)
        old_stage = lead.stage
        lead.stage = STAGE_MAP[serializer.validated_data['stage_id']]
        lead.save()
        note = serializer.validated_data.get('note', '')
        if lead.stage == old_stage and note:
            log(lead, 'note', request.user, note)
        log_stage_change(lead, old_stage, request.user, note)
        return Response(LeadSerializer(lead).data)


class LeadActivityView(APIView):
    """
    GET  /api/leads/<id>/activity/   — every activity, newest first (same entries as /history/)
    POST /api/leads/<id>/activity/   — log a contact: { "action": "call", "note": "Called and confirmed" }
    Action options: call | whatsapp | email | meeting | note
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        from .serializers import LeadActivitySerializer
        return Response(LeadActivitySerializer(LeadActivity.objects.filter(lead=lead), many=True).data)

    def post(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        serializer = LeadActivityWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error(serializer.errors)
        activity = log(lead, serializer.validated_data['action'], request.user,
                       serializer.validated_data.get('note', ''))
        lead.last_contacted = timezone.localdate()
        lead.save(update_fields=['last_contacted', 'updated_at'])
        from .serializers import LeadActivitySerializer
        return Response(LeadActivitySerializer(activity).data, status=201)


# ── History ───────────────────────────────────────────────────────────────────

def _history_item(a):
    return {
        'id':         a.id,
        'type':       a.action,
        'message':    a.note,
        'data':       a.data or {},
        'created_by': {'id': a.created_by_id, 'name': _name(a.created_by)} if a.created_by_id else None,
        'created_at': a.created_at,
    }


class LeadHistoryView(APIView):
    """
    GET /api/leads/<id>/history/?order=asc|desc&type=stage_change,note&page=1&page_size=50
    Everything that happened to the lead, oldest first by default.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        qs = LeadActivity.objects.filter(lead=lead).select_related('created_by')
        order = request.query_params.get('order', 'asc')
        if order not in ('asc', 'desc'):
            return validation_error({'order': 'Use asc or desc.'})
        types = [t.strip() for t in request.query_params.get('type', '').split(',') if t.strip()]
        valid = dict(LeadActivity.ACTION_CHOICES)
        bad = [t for t in types if t not in valid]
        if bad:
            return validation_error({'type': f'Unknown type(s): {", ".join(bad)}.'})
        if types:
            qs = qs.filter(action__in=types)
        qs = qs.order_by('created_at', 'id') if order == 'asc' else qs.order_by('-created_at', '-id')
        from utils.pagination import paginate
        return paginate(request, qs, lambda rows: [_history_item(a) for a in rows])


# ── Notes ─────────────────────────────────────────────────────────────────────

class LeadNotesView(APIView):
    """
    GET  /api/leads/<id>/notes/   — free-text notes, newest first
    POST /api/leads/<id>/notes/   { "text": "Prefers evening calls" }
    Notes also appear in /history/ (type "note").
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        notes = LeadActivity.objects.filter(lead=lead, action='note').select_related('created_by') \
            .order_by('-created_at', '-id')
        return Response([_note(n) for n in notes])

    def post(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        text = str(request.data.get('text', request.data.get('note', '')) or '').strip()
        if not text:
            return validation_error({'text': 'This field is required.'})
        if len(text) > 5000:
            return validation_error({'text': 'Keep notes under 5000 characters.'})
        return Response(_note(log(lead, 'note', request.user, text)), status=201)


def _note(a):
    return {'id': a.id, 'text': a.note,
            'created_by': {'id': a.created_by_id, 'name': _name(a.created_by)} if a.created_by_id else None,
            'created_at': a.created_at}


# ── Tasks ─────────────────────────────────────────────────────────────────────

def _task(t):
    today = timezone.localdate()
    return {
        'id':          t.id,
        'lead_id':     t.lead_id,
        'title':       t.title,
        'due_date':    t.due_date,
        'is_overdue':  bool(t.due_date and not t.is_done and t.due_date < today),
        'is_done':     t.is_done,
        'done_at':     t.done_at,
        'done_by':     {'id': t.done_by_id, 'name': _name(t.done_by)} if t.done_by_id else None,
        'assigned_staff_id':   t.assigned_to_id,
        'assigned_staff_name': _name(t.assigned_to) if t.assigned_to_id else None,
        'created_by':  {'id': t.created_by_id, 'name': _name(t.created_by)} if t.created_by_id else None,
        'created_at':  t.created_at,
        'updated_at':  t.updated_at,
    }


def _apply_task_fields(task, d, errors, creating):
    if creating or 'title' in d:
        title = str(d.get('title', '') or '').strip()
        if not title:
            errors['title'] = 'This field is required.'
        task.title = title[:200]
    if 'due_date' in d:
        raw = d.get('due_date')
        if raw in (None, ''):
            task.due_date = None
        else:
            try:
                task.due_date = datetime.date.fromisoformat(str(raw))
            except ValueError:
                errors['due_date'] = 'Use YYYY-MM-DD.'
    if 'assigned_staff_id' in d:
        raw = d.get('assigned_staff_id')
        if raw in (None, ''):
            task.assigned_to = None
        else:
            from users.models import User
            staff = User.objects.filter(pk=raw, is_active=True).first() if str(raw).isdigit() else None
            if staff is None:
                errors['assigned_staff_id'] = f'Staff member {raw} not found.'
            task.assigned_to = staff


class LeadTasksView(APIView):
    """
    GET  /api/leads/<id>/tasks/?is_done=false   — open first, then by due date
    POST /api/leads/<id>/tasks/   { "title": "Call back with quote", "due_date": "2026-11-25", "assigned_staff_id": 8? }
         assigned_staff_id defaults to the lead's assignee.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        qs = LeadTask.objects.filter(lead=lead).select_related('assigned_to', 'done_by', 'created_by')
        raw = str(request.query_params.get('is_done', '') or '').lower()
        if raw in ('true', 'false'):
            qs = qs.filter(is_done=(raw == 'true'))
        elif raw:
            return validation_error({'is_done': 'Use true or false.'})
        return Response([_task(t) for t in qs])

    def post(self, request, pk):
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        task = LeadTask(lead=lead, created_by=request.user, assigned_to=lead.assigned_to)
        errors = {}
        _apply_task_fields(task, request.data, errors, creating=True)
        if errors:
            return validation_error(errors)
        task.save()
        due = f' (due {task.due_date.isoformat()})' if task.due_date else ''
        log(lead, 'task_created', request.user, f'Task: {task.title}{due}', {'task_id': task.id})
        return Response(_task(task), status=201)


class LeadTaskDetailView(APIView):
    """
    PATCH  /api/leads/<id>/tasks/<task_id>/   { "is_done": true } and/or title, due_date, assigned_staff_id
    DELETE /api/leads/<id>/tasks/<task_id>/
    """
    permission_classes = [IsAdminOrReception]

    def _get(self, pk, task_id):
        lead = _get_lead(pk)
        if not lead:
            return None, lead_not_found()
        task = LeadTask.objects.select_related('assigned_to', 'done_by', 'created_by') \
            .filter(pk=task_id, lead=lead).first()
        if not task:
            return None, error(404, 'task_not_found', 'Task not found.')
        return task, None

    def patch(self, request, pk, task_id):
        task, err = self._get(pk, task_id)
        if err:
            return err
        errors = {}
        _apply_task_fields(task, request.data, errors, creating=False)
        done_changed = False
        if 'is_done' in request.data:
            value = request.data.get('is_done')
            if value not in (True, False, 'true', 'false'):
                errors['is_done'] = 'Use true or false.'
            else:
                value = value in (True, 'true')
                done_changed = value != task.is_done
                task.is_done = value
                task.done_at = timezone.now() if value else None
                task.done_by = request.user if value else None
        if errors:
            return validation_error(errors)
        task.save()
        if done_changed:
            log(task.lead, 'task_completed' if task.is_done else 'task_reopened', request.user,
                f'Task {"done" if task.is_done else "reopened"}: {task.title}', {'task_id': task.id})
        return Response(_task(task))

    def put(self, request, pk, task_id):
        return self.patch(request, pk, task_id)

    def delete(self, request, pk, task_id):
        task, err = self._get(pk, task_id)
        if err:
            return err
        task.delete()
        return Response({'message': 'Task deleted.'})


# ── Conversion ────────────────────────────────────────────────────────────────

class LeadConvertView(APIView):
    """
    POST /api/leads/<id>/convert/   {}  or  { "patient_id": "Aura41" }
    Turns the lead into a patient and stores the link (converted_patient_id). With patient_id,
    links an existing patient instead of creating one. The lead moves to Won.
    409 patient_exists  — a patient with the lead's phone already exists: send its id as patient_id to link it.
    409 already_converted — the lead is already linked to a patient.
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request, pk):
        from patients.models import Patient
        lead = _get_lead(pk)
        if not lead:
            return lead_not_found()
        if lead.converted_patient_id:
            return error(409, 'already_converted', 'This lead has already been converted.',
                         converted_patient_id=lead.converted_patient.patient_id if lead.converted_patient else None)

        raw = str(request.data.get('patient_id', '') or '').strip()
        created = False
        if raw:
            patient = (Patient.objects.filter(pk=int(raw)).first() if raw.isdigit()
                       else Patient.objects.filter(patient_id__iexact=raw).first())
            if patient is None:
                return validation_error({'patient_id': f"Patient '{raw}' not found."})
        else:
            existing = Patient.objects.filter(phone=lead.phone).order_by('id').first() if lead.phone else None
            if existing:
                return error(409, 'patient_exists',
                             'A patient with this phone number already exists. Link the lead to them instead.',
                             existing_patient={'id': existing.patient_id, 'name': existing.name,
                                               'phone': existing.phone})
            patient = Patient.objects.create(
                name=lead.name, phone=lead.phone, email=lead.email or None,
                notes=f"Converted from lead. Source: {lead.source}. {lead.notes}".strip(),
                created_by=request.user,
            )
            created = True

        old_stage = lead.stage
        lead.stage = 'converted'
        lead.converted_patient = patient
        lead.converted_at = timezone.now()
        lead.converted_by = request.user
        lead.save()
        log_stage_change(lead, old_stage, request.user)
        log(lead, 'converted', request.user,
            f"Converted to patient {patient.name} ({patient.patient_id})" + ('' if created else ' — linked to an existing patient'),
            {'patient_id': patient.patient_id, 'patient_db_id': patient.id, 'created_patient': created})
        return Response({
            'message':      'Lead converted to patient successfully.' if created else 'Lead linked to the patient.',
            'patient_id':   patient.id,             # numeric id, unchanged from before
            'converted_patient_id': patient.patient_id,   # Aura id, same as the lead's converted_patient_id
            'patient_name': patient.name,
            'created_patient': created,
            'lead':         _detail(_get_lead(lead.pk)),
        }, status=201)
