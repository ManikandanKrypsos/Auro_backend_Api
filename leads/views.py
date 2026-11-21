import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin, IsAdminOrReception
from .models import Lead, LeadActivity
from .serializers import (
    LeadSerializer, LeadListSerializer, LeadWriteSerializer,
    LeadStageUpdateSerializer, LeadActivityWriteSerializer,
    STAGE_MAP, STAGE_ID_MAP, SOURCE_MAP, scheduled_phones_for,
)


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
            leads = Lead.objects.filter(stage=stage).select_related('assigned_to').order_by('-created_at')
            result.append({
                'stage':       stage,
                'stage_label': label,
                'count':       leads.count(),
                'stage_id':    STAGE_ID_MAP[stage],
                'leads':       LeadListSerializer(leads, many=True, context={'scheduled_phones': scheduled_phones_for(list(leads))}).data,
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
        leads  = Lead.objects.select_related('assigned_to').order_by('-created_at', '-id')
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
            return Response(errors, status=400)

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
                return Response(errors, status=400)
            page_size = max(1, min(page_size, 100))
            paginator = Paginator(leads, page_size)
            page      = paginator.get_page(page_num)
            items     = list(page.object_list)
        else:
            items = list(leads)

        data = LeadListSerializer(
            items, many=True, context={'scheduled_phones': scheduled_phones_for(items)}
        ).data

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
        if serializer.is_valid():
            lead = serializer.save()
            if lead.assigned_to_id:
                from notifications import service as notify
                notify.lead_assigned(lead, request.user)
            return Response(LeadSerializer(lead).data, status=201)
        return Response(serializer.errors, status=400)


class LeadDetailView(APIView):
    """
    GET    /api/leads/<id>/
    PATCH  /api/leads/<id>/
    DELETE /api/leads/<id>/
    """
    def get_permissions(self):
        return [IsAdminOrReception()]

    def _get(self, pk):
        try:
            return Lead.objects.prefetch_related('activities').get(pk=pk)
        except Lead.DoesNotExist:
            return None

    def get(self, request, pk):
        lead = self._get(pk)
        if not lead:
            return Response({'error': 'Lead not found.'}, status=404)
        return Response(LeadSerializer(lead).data)

    def patch(self, request, pk):
        lead = self._get(pk)
        if not lead:
            return Response({'error': 'Lead not found.'}, status=404)
        serializer = LeadWriteSerializer(lead, data=request.data, partial=True)
        if serializer.is_valid():
            assigned_before = lead.assigned_to_id
            lead = serializer.save()
            if lead.assigned_to_id and lead.assigned_to_id != assigned_before:
                from notifications import service as notify
                notify.lead_assigned(lead, request.user)
            return Response(LeadSerializer(lead).data)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        lead = self._get(pk)
        if not lead:
            return Response({'error': 'Lead not found.'}, status=404)
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
        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found.'}, status=404)

        serializer = LeadStageUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        old_stage = lead.stage
        new_stage = STAGE_MAP[serializer.validated_data['stage_id']]
        note      = serializer.validated_data.get('note', '')

        lead.stage = new_stage
        lead.save()

        LeadActivity.objects.create(
            lead=lead,
            action='stage_change',
            note=f"Stage: {old_stage} → {new_stage}. {note}".strip(),
            created_by=request.user
        )
        return Response(LeadSerializer(lead).data)


class LeadActivityView(APIView):
    """
    GET  /api/leads/<id>/activity/   — list all activities for a lead
    POST /api/leads/<id>/activity/   — log a new activity
    Body: { "action": "call", "note": "Called and confirmed" }
    Action options: call | whatsapp | email | meeting | note
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found.'}, status=404)
        from .serializers import LeadActivitySerializer
        activities = LeadActivity.objects.filter(lead=lead)
        return Response(LeadActivitySerializer(activities, many=True).data)

    def post(self, request, pk):
        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found.'}, status=404)

        serializer = LeadActivityWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        activity = LeadActivity.objects.create(
            lead=lead,
            action=serializer.validated_data['action'],
            note=serializer.validated_data.get('note', ''),
            created_by=request.user
        )
        lead.last_contacted = timezone.localdate()
        lead.save()

        from .serializers import LeadActivitySerializer
        return Response(LeadActivitySerializer(activity).data, status=201)


class LeadConvertView(APIView):
    """
    POST /api/leads/<id>/convert/
    Convert a lead to a patient.
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request, pk):
        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found.'}, status=404)

        from patients.models import Patient
        if Patient.objects.filter(phone=lead.phone).exists():
            return Response({'error': 'Patient with this phone already exists.'}, status=400)

        patient = Patient.objects.create(
            name=lead.name,
            phone=lead.phone,
            email=lead.email or '',
            notes=f"Converted from lead. Source: {lead.source}. {lead.notes}",
        )

        lead.stage = 'converted'
        lead.save()

        LeadActivity.objects.create(
            lead=lead,
            action='note',
            note=f"Converted to patient (ID: {patient.id})",
            created_by=request.user
        )

        return Response({
            'message':      'Lead converted to patient successfully.',
            'patient_id':   patient.id,
            'patient_name': patient.name,
        }, status=201)