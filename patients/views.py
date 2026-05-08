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

        # Fetch role fresh from DB
        from users.models import User as UserModel
        try:
            current_user = UserModel.objects.get(pk=self.request.user.pk)
            user_role    = current_user.role or ''
        except Exception:
            user_role = ''

        if user_role == 'therapist':
            from appointments.models import Appointment
            patient_ids = Appointment.objects.filter(
                staff_id=self.request.user.pk
            ).values_list('patient_id', flat=True).distinct()
            qs = qs.filter(id__in=patient_ids)

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
        pk = self.kwargs.get('pk', '')

        if pk and not pk.isdigit():
            try:
                obj = Patient.objects.get(patient_id__iexact=pk)
                self.check_object_permissions(self.request, obj)
                return obj
            except Patient.DoesNotExist:
                raise NotFound(f"Patient '{pk}' not found")

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

    def _handle_image_upload(self, request, patient):
        """Save uploaded image file and update patient.image field."""
        image_file = request.FILES.get('image')
        if image_file:
            import os
            from django.conf import settings
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'patients')
            os.makedirs(upload_dir, exist_ok=True)
            ext      = os.path.splitext(image_file.name)[1].lower()
            filename = f"patient_{patient.id}{ext}"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb+') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            base_url = request.build_absolute_uri('/')
            patient.image = f"{base_url.rstrip('/')}{settings.MEDIA_URL}patients/{filename}"
            patient.save()

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # After create, handle image upload if provided
        if request.FILES.get('image'):
            try:
                patient = Patient.objects.get(patient_id=response.data.get('id'))
                self._handle_image_upload(request, patient)
                response.data['image'] = patient.image
            except Exception:
                pass
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        if request.FILES.get('image'):
            try:
                patient = self.get_object()
                self._handle_image_upload(request, patient)
                response.data['image'] = patient.image
            except Exception:
                pass
        return response

    def destroy(self, request, *args, **kwargs):
        patient = self.get_object()
        patient_id   = patient.patient_id
        patient_name = patient.name
        patient.delete()
        return Response({
            'message':          f'Patient {patient_name} ({patient_id}) deleted successfully',
            'deleted_id':       patient_id,
            'deleted_patient':  patient_name,
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


class PatientVIPView(APIView):
    """
    PATCH /api/patients/<id>/vip/
    Mark or unmark a patient as VIP.
    Body: { "is_vip": true }  or  { "is_vip": false }
    """
    permission_classes = [IsAdminOrReception]

    def _get_patient(self, pk):
        if pk and not str(pk).isdigit():
            try:
                return Patient.objects.get(patient_id__iexact=pk)
            except Patient.DoesNotExist:
                return None
        try:
            return Patient.objects.get(id=int(pk))
        except (Patient.DoesNotExist, ValueError):
            return None

    def patch(self, request, pk):
        patient = self._get_patient(pk)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        is_vip = request.data.get('is_vip', True)

        if is_vip:
            patient.category = 'VIP'
            message = f'{patient.name} marked as VIP.'
        else:
            # Downgrade based on treatment count
            from appointments.models import Appointment
            completed_count = Appointment.objects.filter(
                patient=patient, status='completed'
            ).values('treatment').distinct().count()
            patient.category = 'Returning' if completed_count > 1 else 'New'
            message = f'{patient.name} VIP status removed. Category set to {patient.category}.'

        patient.save()
        return Response({
            'message':    message,
            'patient_id': patient.patient_id,
            'category':   patient.category,
        })