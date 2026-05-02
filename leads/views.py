import datetime
from django.utils import timezone
from django.db.models import Q, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin, IsAdminOrReception
from .models import Lead, LeadActivity
from .serializers import (
    LeadSerializer, LeadWriteSerializer,
    LeadStageUpdateSerializer, LeadActivityWriteSerializer,
    STAGE_MAP, SOURCE_MAP,
)


class LeadMetaView(APIView):
    """
    GET /api/leads/meta/  — all dropdown options with IDs
    """
    def get(self, request):
        return Response({
            'sources': [
                {'id': 1, 'value': 'instagram', 'label': 'Instagram'},
                {'id': 2, 'value': 'web',       'label': 'Web'},
                {'id': 3, 'value': 'walk_in',   'label': 'Walk-In'},
                {'id': 4, 'value': 'referral',  'label': 'Referral'},
                {'id': 5, 'value': 'whatsapp',  'label': 'WhatsApp'},
                {'id': 6, 'value': 'other',     'label': 'Other'},
            ],
            'stages': [
                {'id': 1, 'value': 'new_inquiries', 'label': 'New Inquiries'},
                {'id': 2, 'value': 'engaged',       'label': 'Engaged'},
                {'id': 3, 'value': 'consultation',  'label': 'Consultation'},
                {'id': 4, 'value': 'winning',       'label': 'Winning'},
                {'id': 5, 'value': 'converted',     'label': 'Converted'},
                {'id': 6, 'value': 'lost',          'label': 'Lost'},
            ],
        })


class LeadStatsView(APIView):
    """
    GET /api/leads/stats/
    Returns total leads, active count and total valuation — shown at top of pipeline.
    """
    def get(self, request):
        total      = Lead.objects.count()
        active     = Lead.objects.filter(
            stage__in=['new_inquiries', 'engaged', 'consultation', 'winning']
        ).count()
        valuation  = Lead.objects.aggregate(total=Sum('value'))['total'] or 0

        return Response({
            'total_leads': total,
            'active':      active,
            'valuation':   float(valuation),
        })


class LeadPipelineView(APIView):
    """
    GET /api/leads/pipeline/
    Returns leads grouped by pipeline stage — used for the kanban board.
    """
    def get(self, request):
        pipeline_stages = [
            ('new_inquiries', 'New Inquiries'),
            ('engaged',       'Engaged'),
            ('consultation',  'Consultation'),
            ('winning',       'Winning'),
        ]
        result = []
        for stage, label in pipeline_stages:
            leads = Lead.objects.filter(stage=stage).order_by('-created_at')
            result.append({
                'stage':       stage,
                'stage_label': label,
                'count':       leads.count(),
                'leads':       LeadSerializer(leads, many=True).data,
            })
        return Response(result)


class LeadListView(APIView):
    """
    GET  /api/leads/           — list all leads
         ?search=name/phone    search
         ?stage=engaged        filter by stage
         ?source=instagram     filter by source
    POST /api/leads/           — create new inquiry
    """
    def get_permissions(self):
        return [IsAdminOrReception()]

    def get(self, request):
        leads  = Lead.objects.all()
        search = request.query_params.get('search', '').strip()
        stage  = request.query_params.get('stage', '').strip()
        source = request.query_params.get('source', '').strip()

        if search:
            leads = leads.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        if stage:
            leads = leads.filter(stage=stage)
        if source:
            leads = leads.filter(source=source)

        return Response(LeadSerializer(leads, many=True).data)

    def post(self, request):
        serializer = LeadWriteSerializer(data=request.data)
        if serializer.is_valid():
            lead = serializer.save()
            return Response(LeadSerializer(lead).data, status=201)
        return Response(serializer.errors, status=400)


class LeadDetailView(APIView):
    """
    GET    /api/leads/<id>/
    PATCH  /api/leads/<id>/
    DELETE /api/leads/<id>/
    """
    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAdmin()]
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
            return Response(LeadSerializer(serializer.save()).data)
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