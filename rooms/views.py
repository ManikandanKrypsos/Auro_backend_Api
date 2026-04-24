from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Room
from .serializers import RoomSerializer
from users.permissions import IsAdmin


class RoomListView(APIView):
    """
    GET  /api/rooms/        — list all rooms (optional ?search= ?type=)
    POST /api/rooms/        — add a new room
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        rooms  = Room.objects.all()
        search = request.query_params.get('search', '').strip()
        rtype  = request.query_params.get('type', '').strip()

        if search:
            rooms = rooms.filter(name__icontains=search)
        if rtype:
            rooms = rooms.filter(room_type=rtype)

        return Response(RoomSerializer(rooms, many=True).data)

    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class RoomDetailView(APIView):
    """
    GET    /api/rooms/<id>/  — get a single room
    PATCH  /api/rooms/<id>/  — edit a room
    DELETE /api/rooms/<id>/  — delete a room
    """
    permission_classes = [IsAdmin]

    def _get_room(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            return None

    def get(self, request, pk):
        room = self._get_room(pk)
        if not room:
            return Response({'error': 'Room not found.'}, status=404)
        return Response(RoomSerializer(room).data)

    def patch(self, request, pk):
        room = self._get_room(pk)
        if not room:
            return Response({'error': 'Room not found.'}, status=404)
        serializer = RoomSerializer(room, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        room = self._get_room(pk)
        if not room:
            return Response({'error': 'Room not found.'}, status=404)
        room.delete()
        return Response({'message': 'Room deleted successfully.'})


class RoomTypesView(APIView):
    """
    GET /api/rooms/types/  — list all available room types for the dropdown
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        types = [
            {'value': k, 'label': v}
            for k, v in Room.ROOM_TYPE_CHOICES
        ]
        return Response(types)