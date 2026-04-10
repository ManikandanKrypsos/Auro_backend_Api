from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from users.permissions import IsAdmin
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': UserSerializer(user).data}, status=201)
        return Response(serializer.errors, status=400)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': UserSerializer(user).data})
        return Response(serializer.errors, status=400)

class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class UserListView(APIView):
    permission_classes = [IsAdmin]  # Only admin can see all staff

    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)