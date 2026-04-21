from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from users.permissions import IsAdminOrReception
from .models import Patient
from .serializers import PatientSerializer
from django.db.models import Q


class MarketingSourceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"id": 1, "value": "Instagram", "label": "Instagram"},
            {"id": 2, "value": "Website",   "label": "Website"},
            {"id": 3, "value": "Walk-in",   "label": "Walk-in"},
            {"id": 4, "value": "Referral",  "label": "Referral"},
            {"id": 5, "value": "WhatsApp",  "label": "WhatsApp"},
            {"id": 6, "value": "Other",     "label": "Other"},
        ])


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    filter_backends = []

    def get_queryset(self):
        qs = Patient.objects.all().order_by('-created_at')
        search   = self.request.query_params.get('search', '')
        category = self.request.query_params.get('category', '')

        if search:
            qs = qs.filter(
                Q(name__icontains=search)       |
                Q(phone__istartswith=search)    |
                Q(email__istartswith=search)    |
                Q(patient_id__icontains=search)
            )

        if category:
            qs = qs.filter(category=category)

        return qs

    def get_object(self):
        """
        Support both Aura6 and numeric 6 as lookup
        """
        pk = self.kwargs.get('pk', '')

        # Try patient_id first (Aura6, aura6)
        if pk and not pk.isdigit():
            try:
                obj = Patient.objects.get(patient_id__iexact=pk)
                self.check_object_permissions(self.request, obj)
                return obj
            except Patient.DoesNotExist:
                raise NotFound(f"Patient '{pk}' not found")

        # Try numeric id
        try:
            obj = Patient.objects.get(id=int(pk))
            self.check_object_permissions(self.request, obj)
            return obj
        except (Patient.DoesNotExist, ValueError, TypeError):
            raise NotFound(f"Patient '{pk}' not found")

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrReception()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        patient = self.get_object()
        patient_id = patient.patient_id
        patient_name = patient.name
        patient.delete()
        return Response({
            'message': f'Patient {patient_name} ({patient_id}) deleted successfully',
            'deleted_id': patient_id,
            'deleted_name': patient_name,
        }, status=200)

    @action(detail=False, methods=['get'], url_path='form-choices',
            permission_classes=[IsAuthenticated])
    def form_choices(self, request):
        return Response({
            'gender': [
                {'id': 1, 'value': 'Female', 'label': 'Female'},
                {'id': 2, 'value': 'Male',   'label': 'Male'},
                {'id': 3, 'value': 'Other',  'label': 'Other'},
            ],
            'skin_type': [
                {'id': 1, 'value': 'Normal',      'label': 'Normal'},
                {'id': 2, 'value': 'Dry',         'label': 'Dry'},
                {'id': 3, 'value': 'Oily',        'label': 'Oily'},
                {'id': 4, 'value': 'Combination', 'label': 'Combination'},
                {'id': 5, 'value': 'Sensitive',   'label': 'Sensitive'},
            ],
            'blood_type': [
                {'id': 1, 'value': 'A+',  'label': 'A+'},
                {'id': 2, 'value': 'A-',  'label': 'A-'},
                {'id': 3, 'value': 'B+',  'label': 'B+'},
                {'id': 4, 'value': 'B-',  'label': 'B-'},
                {'id': 5, 'value': 'AB+', 'label': 'AB+'},
                {'id': 6, 'value': 'AB-', 'label': 'AB-'},
                {'id': 7, 'value': 'O+',  'label': 'O+'},
                {'id': 8, 'value': 'O-',  'label': 'O-'},
            ],
            'marketing_source': [
                {'id': 1, 'value': 'Instagram', 'label': 'Instagram'},
                {'id': 2, 'value': 'Website',   'label': 'Website'},
                {'id': 3, 'value': 'Walk-in',   'label': 'Walk-in'},
                {'id': 4, 'value': 'Referral',  'label': 'Referral'},
                {'id': 5, 'value': 'WhatsApp',  'label': 'WhatsApp'},
                {'id': 6, 'value': 'Other',     'label': 'Other'},
            ],
            'category': [
                {'id': 1, 'value': 'New',       'label': 'New'},
                {'id': 2, 'value': 'Returning', 'label': 'Returning'},
                {'id': 3, 'value': 'VIP',       'label': 'VIP'},
                {'id': 4, 'value': 'Lead',      'label': 'Lead'},
            ],
        })