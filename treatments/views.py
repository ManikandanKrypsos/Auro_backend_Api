from rest_framework.views import APIView
from rest_framework.response import Response
from users.permissions import IsAdmin, IsAdminOrReadOnly
from .models import Treatment, PricePlan
from .serializers import TreatmentSerializer, TreatmentWriteSerializer, PricePlanSerializer


class TreatmentListView(APIView):
    """
    GET  /api/treatments/         — list all treatments (?search= ?category=face|body)
    POST /api/treatments/         — create treatment
    """
    def get_permissions(self):
        return [IsAdmin()] if self.request.method == 'POST' else [IsAdminOrReadOnly()]

    def get(self, request):
        treatments = Treatment.objects.prefetch_related('price_plans', 'staff').all()
        search   = request.query_params.get('search', '').strip()
        category = request.query_params.get('category', '').strip()
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
    GET    /api/treatments/<id>/
    PATCH  /api/treatments/<id>/
    DELETE /api/treatments/<id>/
    """
    def get_permissions(self):
        return [IsAdmin()] if self.request.method in ['PATCH', 'PUT', 'DELETE'] else [IsAdminOrReadOnly()]

    def _get(self, pk):
        try:
            return Treatment.objects.prefetch_related('price_plans', 'staff').get(pk=pk)
        except Treatment.DoesNotExist:
            return None

    def get(self, request, pk):
        t = self._get(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        return Response(TreatmentSerializer(t).data)

    def _update(self, request, pk):
        t = self._get(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        serializer = TreatmentWriteSerializer(t, data=request.data, partial=True)
        if serializer.is_valid():
            return Response(TreatmentSerializer(serializer.save()).data)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        return self._update(request, pk)

    def put(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        t = self._get(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        t.delete()
        return Response({'message': 'Treatment deleted successfully.'})


# ── Price Plans ───────────────────────────────────────────────────────────────

class PricePlanListView(APIView):
    """
    GET  /api/treatments/<id>/price-plans/    — list price plans
    POST /api/treatments/<id>/price-plans/    — add a price plan
    Body: { "sessions": 5, "price": 450 }
    """
    permission_classes = [IsAdmin]

    def _get_treatment(self, pk):
        try:
            return Treatment.objects.get(pk=pk)
        except Treatment.DoesNotExist:
            return None

    def get(self, request, pk):
        t = self._get_treatment(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        return Response(PricePlanSerializer(t.price_plans.all(), many=True).data)

    def post(self, request, pk):
        t = self._get_treatment(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        serializer = PricePlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(treatment=t)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class PricePlanDetailView(APIView):
    """
    PATCH  /api/treatments/<id>/price-plans/<plan_id>/  — edit plan
    DELETE /api/treatments/<id>/price-plans/<plan_id>/  — delete plan
    """
    permission_classes = [IsAdmin]

    def _get_plan(self, pk, plan_id):
        try:
            return PricePlan.objects.get(pk=plan_id, treatment_id=pk)
        except PricePlan.DoesNotExist:
            return None

    def patch(self, request, pk, plan_id):
        plan = self._get_plan(pk, plan_id)
        if not plan:
            return Response({'error': 'Price plan not found.'}, status=404)
        serializer = PricePlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def put(self, request, pk, plan_id):
        return self.patch(request, pk, plan_id)

    def delete(self, request, pk, plan_id):
        plan = self._get_plan(pk, plan_id)
        if not plan:
            return Response({'error': 'Price plan not found.'}, status=404)
        plan.delete()
        return Response({'message': 'Price plan deleted successfully.'})


# ── Contraindications ─────────────────────────────────────────────────────────

class ContraindicationView(APIView):
    """
    GET  /api/treatments/<id>/contraindications/
         Returns the list of contraindications for a treatment.

    POST /api/treatments/<id>/contraindications/
         Add one or more contraindications.
         Body: { "items": ["Pregnancy", "Active acne"] }

    DELETE /api/treatments/<id>/contraindications/
         Remove a specific contraindication.
         Body: { "item": "Pregnancy" }

    PUT /api/treatments/<id>/contraindications/
        Replace entire contraindications list.
        Body: { "items": ["Pregnancy", "Rosacea"] }
    """
    permission_classes = [IsAdmin]

    def _get_treatment(self, pk):
        try:
            return Treatment.objects.get(pk=pk)
        except Treatment.DoesNotExist:
            return None

    def get(self, request, pk):
        t = self._get_treatment(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        return Response({'contraindications': t.contraindications or []})

    def post(self, request, pk):
        t = self._get_treatment(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        items = request.data.get('items', [])
        if not isinstance(items, list) or not items:
            return Response({'error': 'Provide items as a non-empty list.'}, status=400)
        existing = t.contraindications or []
        # Add only new ones
        for item in items:
            if item not in existing:
                existing.append(item)
        t.contraindications = existing
        t.save()
        return Response({'contraindications': t.contraindications}, status=201)

    def put(self, request, pk):
        t = self._get_treatment(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        items = request.data.get('items', [])
        if not isinstance(items, list):
            return Response({'error': 'Provide items as a list.'}, status=400)
        t.contraindications = items
        t.save()
        return Response({'contraindications': t.contraindications})

    def delete(self, request, pk):
        t = self._get_treatment(pk)
        if not t:
            return Response({'error': 'Treatment not found.'}, status=404)
        item = request.data.get('item', '').strip()
        if not item:
            return Response({'error': 'Provide item to remove.'}, status=400)
        existing = t.contraindications or []
        if item not in existing:
            return Response({'error': f'"{item}" not found in contraindications.'}, status=404)
        existing.remove(item)
        t.contraindications = existing
        t.save()
        return Response({'message': f'"{item}" removed.', 'contraindications': t.contraindications})


class TreatmentMetaView(APIView):
    """GET /api/treatments/meta/"""
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