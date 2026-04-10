from rest_framework import viewsets
from users.permissions import IsAdminOrReadOnly
from .models import Treatment
from .serializers import TreatmentSerializer

class TreatmentViewSet(viewsets.ModelViewSet):
    """
    Admin only: create, edit, delete treatments
    Everyone: can read the treatments list
    """
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsAdminOrReadOnly]