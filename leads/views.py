from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from users.permissions import IsAdmin, IsAdminOrReception
from .models import Lead, LeadActivity
from .serializers import LeadSerializer, LeadActivitySerializer, LeadStageUpdateSerializer
import datetime


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone', 'email', 'source', 'stage']

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdmin()]
        return [IsAdminOrReception()]

    @action(detail=False, methods=['get'], url_path='pipeline')
    def pipeline(self, request):
        # ✅ Fixed: use 'converted' not 'booked'
        stages = ['new', 'contacted', 'consultation', 'converted', 'returning', 'vip', 'lost']
        pipeline = {}
        for stage in stages:
            leads = Lead.objects.filter(stage=stage).order_by('-created_at')
            pipeline[stage] = {
                'count': leads.count(),
                'leads': LeadSerializer(leads, many=True).data
            }
        return Response(pipeline)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        total = Lead.objects.count()
        by_stage = {}
        for stage, _ in Lead.STAGE_CHOICES:
            count = Lead.objects.filter(stage=stage).count()
            by_stage[stage] = {
                'count': count,
                'percentage': round((count / total * 100), 1) if total > 0 else 0
            }

        by_source = {}
        for source, _ in Lead.SOURCE_CHOICES:
            by_source[source] = Lead.objects.filter(source=source).count()

        # ✅ Fixed: use 'converted' not 'booked'
        converted = Lead.objects.filter(stage__in=['converted', 'returning', 'vip']).count()
        conversion_rate = round((converted / total * 100), 1) if total > 0 else 0

        return Response({
            'total_leads':     total,
            'conversion_rate': f'{conversion_rate}%',
            'by_stage':        by_stage,
            'by_source':       by_source,
        })

    @action(detail=True, methods=['patch'], url_path='stage')
    def update_stage(self, request, pk=None):
        lead = self.get_object()
        serializer = LeadStageUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        old_stage = lead.stage
        new_stage = serializer.validated_data['stage']
        note      = serializer.validated_data.get('note', '')

        lead.stage = new_stage
        lead.updated_at = timezone.now()
        lead.save()

        LeadActivity.objects.create(
            lead=lead,
            action='stage_change',
            note=f"Stage changed: {old_stage} → {new_stage}. {note}",
            created_by=request.user
        )
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=['post'], url_path='activity')
    def add_activity(self, request, pk=None):
        lead = self.get_object()
        serializer = LeadActivitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        activity = serializer.save(lead=lead, created_by=request.user)
        lead.last_contacted = timezone.localdate()
        lead.save()
        return Response(LeadActivitySerializer(activity).data, status=201)

    @action(detail=False, methods=['get'], url_path='cold')
    def cold_leads(self, request):
        fourteen_days_ago = timezone.localdate() - datetime.timedelta(days=14)
        cold = Lead.objects.filter(
            stage__in=['new', 'contacted', 'consultation'],
        ).filter(
            Q(last_contacted__lte=fourteen_days_ago) |
            Q(last_contacted__isnull=True)
        ).order_by('last_contacted')

        return Response({
            'count': cold.count(),
            'leads': LeadSerializer(cold, many=True).data
        })

    @action(detail=True, methods=['post'], url_path='convert-to-patient')
    def convert_to_patient(self, request, pk=None):
        lead = self.get_object()
        from patients.models import Patient

        if Patient.objects.filter(phone=lead.phone).exists():
            return Response({'error': 'Patient with this phone already exists'}, status=400)

        patient = Patient.objects.create(
            name=lead.name,
            phone=lead.phone,
            email=lead.email or '',
            notes=f"Converted from lead. Source: {lead.source}. {lead.notes}",
            tags='New'
        )

        # ✅ Fixed: use 'converted' not 'booked'
        lead.stage = 'converted'
        lead.save()

        LeadActivity.objects.create(
            lead=lead,
            action='note',
            note=f"Converted to patient (ID: {patient.id})",
            created_by=request.user
        )

        return Response({
            'message':      'Lead converted to patient successfully',
            'patient_id':   patient.id,
            'patient_name': patient.name
        }, status=201)