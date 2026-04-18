from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminOrReception
from .models import Patient
from .serializers import PatientSerializer
from django.db.models import Q


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone', 'email']

    def get_queryset(self):
        qs = Patient.objects.all().order_by('-created_at')

        search = self.request.query_params.get('search', '')
        category = self.request.query_params.get('category', '')

        if search:
            qs = qs.filter(
                Q(name__istartswith=search) |    # 👈 starts with search
                Q(phone__istartswith=search) |   # 👈 phone starts with search
                Q(email__istartswith=search)     # 👈 email starts with search
            )

        if category:
            qs = qs.filter(category=category)

        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrReception()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='form-choices',
            permission_classes=[IsAuthenticated])
    def form_choices(self, request):
        """GET /api/patients/form-choices/ — all dropdown options"""
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