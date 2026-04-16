from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from users.permissions import IsAdmin
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User

ROLE_ID_MAP = {
    'admin':     1,
    'reception': 2,
    'therapist': 3,
    'client':    4,
}

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }

class RolesListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response([
            {"id": 1, "role": "admin",     "title": "Admin",        "level": "LEVEL: EXECUTIVE"},
            {"id": 2, "role": "reception", "title": "Receptionist", "level": "LEVEL: OPERATIONS"},
            {"id": 3, "role": "therapist", "title": "Therapist",    "level": "LEVEL: CLINICAL"},
            {"id": 4, "role": "client",    "title": "Client",       "level": "LEVEL: CLIENT"},
        ])


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'token':         tokens['access'],   # 👈 Bearer JWT
                'refresh_token': tokens['refresh'],
                'role_id':       ROLE_ID_MAP.get(user.role, 1),
                'role':          user.role,
                'user': {
                    'id':      user.id,
                    'username': user.username,
                    'email':   user.email,
                    'role':    user.role,
                    'role_id': ROLE_ID_MAP.get(user.role, 1),
                }
            }, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.validated_data
            tokens = get_tokens_for_user(user)
            return Response({
                'token':         tokens['access'],   # 👈 Bearer JWT
                'refresh_token': tokens['refresh'],
                'role_id':       ROLE_ID_MAP.get(user.role, 1),
                'role':          user.role,
                'user': {
                    'id':      user.id,
                    'username': user.username,
                    'email':   user.email,
                    'role':    user.role,
                    'role_id': ROLE_ID_MAP.get(user.role, 1),
                }
            })
        return Response(serializer.errors, status=400)


class RefreshTokenView(APIView):
    """POST /api/users/refresh/ — get new access token using refresh token"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            refresh = RefreshToken(request.data.get('refresh_token'))
            return Response({'token': str(refresh.access_token)})
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=400)


class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response({
            'id':      user.id,
            'username': user.username,
            'email':   user.email,
            'role':    user.role,
            'role_id': ROLE_ID_MAP.get(user.role, 1),
        })


class UserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)