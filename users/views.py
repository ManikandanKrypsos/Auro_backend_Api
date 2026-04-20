from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from users.permissions import IsAdmin
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
import random
import string


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
                'token':         tokens['access'],
                'refresh_token': tokens['refresh'],
                'role_id':       ROLE_ID_MAP.get(user.role, 1),
                'role':          user.role,
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
            user   = serializer.validated_data
            tokens = get_tokens_for_user(user)
            return Response({
                'token':         tokens['access'],
                'refresh_token': tokens['refresh'],
                'role_id':       ROLE_ID_MAP.get(user.role, 1),
                'role':          user.role,
                'user': {
                    'id':       user.id,
                    'username': user.username,
                    'email':    user.email,
                    'role':     user.role,
                    'role_id':  ROLE_ID_MAP.get(user.role, 1),
                }
            })
        return Response(serializer.errors, status=400)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except TokenError:
            return Response({'error': 'Invalid token'}, status=400)
        except Exception:
            return Response({'error': 'Something went wrong'}, status=400)


class RefreshTokenView(APIView):
    """
    POST /api/users/refresh/
    Send refresh_token → get new access token
    Use this on app start to keep user logged in
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'refresh_token is required'}, status=400)

            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)

            # Get user info
            user_id = refresh.payload.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                return Response({
                    'token':   new_access,
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
            except User.DoesNotExist:
                return Response({'token': new_access})

        except TokenError:
            return Response(
                {'error': 'Token expired or invalid. Please login again.'},
                status=401
            )


class MeView(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=401)
        return Response({
            'id':       user.id,
            'username': user.username,
            'email':    user.email,
            'role':     user.role,
            'role_id':  ROLE_ID_MAP.get(user.role, 1),
        })


class UserListView(APIView):
    """
    GET /api/users/staff/
    GET /api/users/staff/?role=therapist
    GET /api/users/staff/?search=john
    Excludes admin and client — only reception and therapist
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        role   = request.query_params.get('role', '')
        search = request.query_params.get('search', '')

        # 👈 Only show reception and therapist — exclude admin and client
        users = User.objects.filter(
            role__in=['reception', 'therapist']
        )

        if role and role in ['reception', 'therapist']:
            users = users.filter(role=role)

        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__istartswith=search)
            )

        result = []
        for u in users:
            result.append({
                'id':       u.id,
                'username': u.username or u.email.split('@')[0],
                'email':    u.email,
                'role':     u.role,
                'role_id':  ROLE_ID_MAP.get(u.role, 1),
            })
        return Response(result)


class ForgotPasswordView(APIView):
    """
    POST /api/users/forgot-password/
    Body: {"email": "user@aura.com"}
    Sends OTP to email
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'error': 'Email is required'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists — security best practice
            return Response({
                'message': 'If this email exists, an OTP has been sent.'
            })

        # Generate 6 digit OTP
        otp = ''.join(random.choices(string.digits, k=6))

        # Store OTP in user's password reset field (temp solution)
        # In production use a separate OTPModel or cache
        user.set_password(otp)  # temporarily store OTP as password
        # Actually let's store it properly
        from django.core.cache import cache
        cache_key = f'password_reset_otp_{email}'
        cache.set(cache_key, otp, timeout=600)  # 10 minutes

        # Send email
        try:
            send_mail(
                subject='Aura Clinic — Password Reset OTP',
                message=f'''
Hi {user.username or user.email},

Your OTP for password reset is: {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.

— Aura Clinic Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email error: {e}")
            return Response({'error': 'Failed to send email. Try again.'}, status=500)

        return Response({
            'message': 'OTP sent to your email successfully',
            'email':   email
        })


class VerifyOTPView(APIView):
    """
    POST /api/users/verify-otp/
    Body: {"email": "user@aura.com", "otp": "123456"}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        otp   = request.data.get('otp', '').strip()

        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=400)

        from django.core.cache import cache
        cache_key = f'password_reset_otp_{email}'
        stored_otp = cache.get(cache_key)

        if not stored_otp:
            return Response({'error': 'OTP expired. Please request a new one.'}, status=400)

        if stored_otp != otp:
            return Response({'error': 'Invalid OTP'}, status=400)

        # OTP valid — generate reset token
        try:
            user = User.objects.get(email=email)
            tokens = get_tokens_for_user(user)
            # Clear OTP from cache
            cache.delete(cache_key)
            return Response({
                'message':      'OTP verified successfully',
                'reset_token':  tokens['access'],  # use as reset token
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class ResetPasswordView(APIView):
    """
    POST /api/users/reset-password/
    Body: {"email": "user@aura.com", "new_password": "newpass123", "confirm_password": "newpass123"}
    Header: Authorization: Bearer reset_token
    """
    def post(self, request):
        new_password     = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if not new_password or not confirm_password:
            return Response({'error': 'Both password fields are required'}, status=400)

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=400)

        if len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=400)

        user = request.user
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password reset successfully. Please login again.'})