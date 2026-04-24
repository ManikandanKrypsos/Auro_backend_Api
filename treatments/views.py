from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin, IsAdminOrReadOnly
from .models import Treatment
from .serializers import TreatmentSerializer, TreatmentWriteSerializer


class TreatmentListView(APIView):
    """
    GET  /api/treatments/          — list all treatments
         ?search=  filter by name
         ?category=face|body
    POST /api/treatments/          — create a new treatment
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAdminOrReadOnly()]

    def get(self, request):
        treatments = Treatment.objects.prefetch_related('price_plans', 'staff').all()
        search     = request.query_params.get('search', '').strip()
        category   = request.query_params.get('category', '').strip()

        if search:
            treatments = treatments.filter(name__icontains=search)
        if category:
            treatments = treatments.filter(category=category)

        return Response(TreatmentSerializer(treatments, many=True).data)

    def post(self, request):
        serializer = TreatmentWriteSerializer(data=request.data)
        if serializer.is_valid():
            treatment = serializer.save()
            return Response(TreatmentSerializer(treatment).data, status=201)
        return Response(serializer.errors, status=400)


class TreatmentDetailView(APIView):
    """
    GET    /api/treatments/<id>/   — get single treatment
    PATCH  /api/treatments/<id>/   — edit treatment (all fields optional)
    PUT    /api/treatments/<id>/   — same as PATCH
    DELETE /api/treatments/<id>/   — delete treatment
    """
    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAdmin()]
        return [IsAdminOrReadOnly()]

    def _get_treatment(self, pk):
        try:
            return Treatment.objects.prefetch_related('price_plans', 'staff').get(pk=pk)
        except Treatment.DoesNotExist:
            return None

    def get(self, request, pk):
        treatment = self._get_treatment(pk)
        if not treatment:
            return Response({'error': 'Treatment not found.'}, status=404)
        return Response(TreatmentSerializer(treatment).data)

    def _update(self, request, pk):
        treatment = self._get_treatment(pk)
        if not treatment:
            return Response({'error': 'Treatment not found.'}, status=404)
        serializer = TreatmentWriteSerializer(treatment, data=request.data, partial=True)
        if serializer.is_valid():
            treatment = serializer.save()
            return Response(TreatmentSerializer(treatment).data)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        return self._update(request, pk)

    def put(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        treatment = self._get_treatment(pk)
        if not treatment:
            return Response({'error': 'Treatment not found.'}, status=404)
        treatment.delete()
        return Response({'message': 'Treatment deleted successfully.'})


class TreatmentMetaView(APIView):
    """
    GET /api/treatments/meta/  — returns all dropdown options with IDs
    """
    def get(self, request):
        return Response({
            'categories': [
                {'id': 1, 'value': 'face', 'label': 'Face'},
                {'id': 2, 'value': 'body', 'label': 'Body'},
            ],
            'room_types': [
                {'id': 1, 'value': 'facial_treatment', 'label': 'Facial Treatment Room'},
                {'id': 2, 'value': 'body_treatment',   'label': 'Body Treatment Room'},
            ],
            'frequency_units': [
                {'id': 1, 'value': 'days',   'label': 'Days'},
                {'id': 2, 'value': 'weeks',  'label': 'Weeks'},
                {'id': 3, 'value': 'months', 'label': 'Months'},
            ],
        })