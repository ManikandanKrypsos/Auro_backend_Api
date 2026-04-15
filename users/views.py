from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from users.permissions import IsAdmin
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User

ROLE_ID_MAP = {
    'admin':     1,
    'reception': 2,
    'therapist': 3,
    'client':    4,
}

class RolesListView(APIView):
    """
    GET /api/users/roles/
    Returns list of roles — Flutter uses this to populate
    the Select Role dropdown on signup screen.
    No authentication required.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        roles = [
            {"id": 1, "role": "admin",      "title": "Admin",        "level": "LEVEL: EXECUTIVE"},
            {"id": 2, "role": "reception",  "title": "Receptionist", "level": "LEVEL: OPERATIONS"},
            {"id": 3, "role": "therapist",  "title": "Therapist",    "level": "LEVEL: CLINICAL"},
            {"id": 4, "role": "client",     "title": "Client",       "level": "LEVEL: CLIENT"},
        ]
        return Response(roles)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token':   token.key,
                'role_id': ROLE_ID_MAP.get(user.role, 1),
                'role':    user.role,
                'user': {
                    'id':       user.id,
                    'username': user.username,
                    'email':    user.email,
                    'role':     user.role,
                    'role_id':  ROLE_ID_MAP.get(user.role, 1),
                }
            }, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token':   token.key,
                'role_id': ROLE_ID_MAP.get(user.role, 1),
                'role':    user.role,
                'user': {
                    'id':       user.id,
                    'username': user.username,
                    'email':    user.email,
                    'role':     user.role,
                    'role_id':  ROLE_ID_MAP.get(user.role, 1),
                }
            })
        return Response(serializer.errors, status=400)


class MeView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        user = request.user
        return Response({
            'id':       user.id,
            'username': user.username,
            'email':    user.email,
            'role':     user.role,
            'role_id':  ROLE_ID_MAP.get(user.role, 1),
        })


class UserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)