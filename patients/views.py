from rest_framework import viewsets, filters
from users.permissions import IsAdminOrReception
from .models import Patient
from .serializers import PatientSerializer

class PatientViewSet(viewsets.ModelViewSet):
    """
    Admin + Reception: full access (create, edit, delete)
    Therapist: read-only (they can view patients, not edit)
    """
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone', 'email', 'tags']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrReception()]
        return super().get_permissions()  # IsAuthenticated for read