from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
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
    filter_backends = []  # 👈 remove default filter — using custom get_queryset

    def get_queryset(self):
        qs = Patient.objects.all().order_by('-created_at')
        search   = self.request.query_params.get('search', '')
        category = self.request.query_params.get('category', '')

        if search:
            qs = qs.filter(
                Q(name__icontains=search)       |   # 👈 icontains for anywhere in string
                Q(phone__istartswith=search)    |
                Q(email__istartswith=search)    |
                Q(patient_id__icontains=search)     # 👈 Aura6, aura6, AURA6 all work
            )

        if category:
            qs = qs.filter(category=category)

        return qs

    def get_object(self):
        """
        Override to support both:
        - /api/patients/Aura6/  (patient_id)
        - /api/patients/6/      (numeric id)
        """
        pk = self.kwargs.get('pk')
        queryset = self.get_queryset()

        # Try patient_id first (e.g. Aura6)
        if pk and not pk.isdigit():
            try:
                obj = Patient.objects.get(patient_id__iexact=pk)
                self.check_object_permissions(self.request, obj)
                return obj
            except Patient.DoesNotExist:
                pass

        # Try numeric id
        try:
            obj = Patient.objects.get(id=pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except (Patient.DoesNotExist, ValueError):
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Patient '{pk}' not found")

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrReception()]
        return [IsAuthenticated()]

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