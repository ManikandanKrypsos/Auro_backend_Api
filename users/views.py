from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from users.permissions import IsAdmin, IsClinicStaff
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, StaffUpdateSerializer
from .models import User
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import os
import hmac
import secrets
from django.core import signing
from django.core.cache import cache
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

RESET_SALT        = 'aura-password-reset'
RESET_MAX_AGE     = 15 * 60      # reset token valid 15 minutes
OTP_TTL           = 10 * 60      # OTP valid 10 minutes
OTP_MAX_ATTEMPTS  = 5
OTP_RESEND_WAIT   = 60           # seconds between OTP emails to the same address
GENERIC_OTP_MSG   = 'If this email is registered, an OTP has been sent.'


ROLE_ID_MAP = {
    'admin':     1,
    'reception': 2,
    'therapist': 3,
}


def _safe_image(url):
    """Return None if image file doesn't exist on disk (deleted by Render redeploy)."""
    if not url:
        return None
    if not url.startswith('http'):
        return None
    if 'auro-backend-api.onrender.com' in url and '/media/' in url:
        try:
            relative = url.split('/media/', 1)[1]
            abs_path = os.path.join(settings.MEDIA_ROOT, relative)
            if not os.path.exists(abs_path):
                return None
        except Exception:
            return None
    return url


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

        ])


class RegisterView(APIView):
    """
    POST /api/users/register/  — retired.
    Clinic admins register with POST /api/clinics/register/ (creates the clinic + its first admin).
    Receptionists and therapists are created by their clinic admin with POST /api/users/staff/.
    """
    permission_classes     = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope         = 'auth'

    def post(self, request):
        role_id = str(request.data.get('role_id', ''))
        if role_id in ('2', '3'):
            return Response({'error': 'Receptionist and therapist accounts are created by your clinic admin.',
                             'code': 'signup_disabled'}, status=403)
        return Response({'error': 'To create a new clinic account, use clinic registration.',
                         'code': 'use_clinic_registration', 'endpoint': '/api/clinics/register/'}, status=403)


def auth_payload(user, tokens=None):
    """Login / registration / refresh response: tokens + user + clinic + password flag."""
    tokens = tokens or get_tokens_for_user(user)
    clinic = user.clinic
    data = {
        'token':         tokens['access'],
        'role_id':       ROLE_ID_MAP.get(user.role, 1),
        'role':          user.role,
        'clinic_id':     clinic.id if clinic else None,
        'clinic_name':   clinic.name if clinic else None,
        'must_change_password': user.must_change_password,
        'user': {
            'id':            user.id,
            'username':      user.username,
            'email':         user.email,
            'role':          user.role,
            'role_id':       ROLE_ID_MAP.get(user.role, 1),
            'profile_image': _safe_image(user.profile_image),
            'clinic_id':     clinic.id if clinic else None,
            'clinic_name':   clinic.name if clinic else None,
            'must_change_password': user.must_change_password,
        },
    }
    if tokens.get('refresh'):
        data['refresh_token'] = tokens['refresh']
    data['billing'] = _billing(clinic)
    return data


def _billing(clinic):
    if clinic is None:
        return None
    from tenants.billing import billing_payload, refresh_trial_status
    return billing_payload(refresh_trial_status(clinic))


def _login_block(user):
    """Response blocking a login/refresh for this user (suspended clinic / no clinic), or None."""
    from tenants.auth import check_clinic_user
    from rest_framework.exceptions import APIException
    try:
        check_clinic_user(user)
    except APIException as e:
        return Response(e.detail, status=e.status_code)
    return None


class LoginView(APIView):
    permission_classes     = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope         = 'auth'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data

            # Block reception/therapist if they are not in the active staff list
            if user.role in ['reception', 'therapist']:
                if not User.all_objects.filter(
                    id=user.id,
                    role__in=['reception', 'therapist']
                ).exists():
                    return Response(
                        {'error': 'Your account is not active. Please contact your admin.', 'code': 'account_inactive'},
                        status=403
                    )
                # Check if account is active (not deleted from staff)
                if not user.is_active:
                    return Response(
                        {'error': 'Your account has been deactivated. Please contact your admin.', 'code': 'account_deactivated'},
                        status=403
                    )

            if not user.is_active:
                return Response({'error': 'Your account has been deactivated. Please contact your admin.',
                                 'code': 'account_deactivated'}, status=403)
            blocked = _login_block(user)
            if blocked:
                return blocked
            return Response(auth_payload(user))
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
    throttle_scope         = 'auth'
    permission_classes     = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'refresh_token is required'}, status=400)

            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)

            user = User.all_objects.filter(id=refresh.payload.get('user_id'), is_active=True).first()
            if not user:
                return Response({'error': 'Account not found or deactivated. Please login again.'}, status=401)
            blocked = _login_block(user)
            if blocked:
                return blocked
            return Response(auth_payload(user, {'access': new_access}))

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
        from users.models import User as UserModel
        try:
            u = UserModel.objects.get(pk=user.pk)
        except Exception:
            u = user
        return Response({
            'id':                  u.id,
            'username':            u.username,
            'email':               u.email,
            'role':                u.role,
            'role_id':             ROLE_ID_MAP.get(u.role, 1),
            'profile_image':       _safe_image(u.profile_image),
            'phone':               u.phone if hasattr(u, 'phone') else None,
            'specialist_area':     u.specialist_area if hasattr(u, 'specialist_area') else None,
            'years_of_experience': u.years_of_experience if hasattr(u, 'years_of_experience') else None,
            'joining_date':        str(u.joining_date) if hasattr(u, 'joining_date') and u.joining_date else None,
            'clinic_id':           u.clinic_id,
            'clinic_name':         u.clinic.name if u.clinic_id else None,
            'must_change_password': u.must_change_password,
            'billing':             _billing(u.clinic) if u.clinic_id else None,
        })

    def patch(self, request):
        """
        PATCH /api/users/me/
        Update own profile. Send as multipart/form-data for image upload.
        Fields: profile_image (file), username, phone, specialist_area,
                years_of_experience, joining_date
        """
        from users.models import User as UserModel
        try:
            user = UserModel.objects.get(pk=request.user.pk)
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        # Handle image file upload
        image_file = request.FILES.get('profile_image')
        if image_file:
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'staff')
            os.makedirs(upload_dir, exist_ok=True)
            from utils.upload_security import checked_ext, random_token
            ext      = checked_ext(image_file, 'image')
            filename = f"staff_{user.id}_{random_token()}{ext}"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb+') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            base_url = request.build_absolute_uri('/')
            user.profile_image = f"{base_url.rstrip('/')}{settings.MEDIA_URL}staff/{filename}"

        # Update other fields
        for field in ['username', 'phone', 'specialist_area', 'years_of_experience', 'joining_date']:
            if field in request.data:
                setattr(user, field, request.data[field])

        user.save()

        return Response({
            'id':                  user.id,
            'username':            user.username,
            'email':               user.email,
            'role':                user.role,
            'role_id':             ROLE_ID_MAP.get(user.role, 1),
            'profile_image':       _safe_image(user.profile_image),
            'phone':               user.phone if hasattr(user, 'phone') else None,
            'specialist_area':     user.specialist_area if hasattr(user, 'specialist_area') else None,
            'years_of_experience': user.years_of_experience if hasattr(user, 'years_of_experience') else None,
            'joining_date':        str(user.joining_date) if hasattr(user, 'joining_date') and user.joining_date else None,
            'clinic_id':           user.clinic_id,
            'clinic_name':         user.clinic.name if user.clinic_id else None,
            'must_change_password': user.must_change_password,
        })


class UserListView(APIView):
    """
    GET /api/users/staff/
    GET /api/users/staff/?role=therapist
    GET /api/users/staff/?role=reception
    GET /api/users/staff/?search=john
    GET /api/users/staff/?page=1&page_size=20   optional pagination (max 100) → {count, page, page_size, total_pages, results}
    Excludes admin — only active reception and therapist
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role   = request.query_params.get('role', '').strip().lower()
        search = request.query_params.get('search', '').strip()

        users = User.objects.filter(
            role__in=['reception', 'therapist'],
            is_active=True
        )

        if role in ['reception', 'therapist']:
            users = users.filter(role=role)

        if search:
            # Match name (startswith) OR email (startswith) — for live search as user types
            users = users.filter(
                Q(username__istartswith=search) |
                Q(email__istartswith=search)
            )

        from utils.pagination import paginate
        return paginate(request, users.order_by('id'), lambda rows: [_format_staff(u) for u in rows])


    def post(self, request):
        """
        POST /api/users/staff/  — admin only. Creates a receptionist or therapist in the admin's
        own clinic with a temporary password (returned once, in this response).
        Body: {"username": "Ebin", "email": "ebin@clinic.com", "role": "therapist" | "reception",
               "phone"?: "...", "specialist_area"?: "..."}      (role_id 2 / 3 also accepted)
        """
        if getattr(request.user, 'role', '') != 'admin':
            return Response({'error': 'Only a clinic admin can create staff accounts.', 'code': 'admin_only'}, status=403)
        d = request.data
        role = str(d.get('role', '') or '').strip().lower()
        role = {'2': 'reception', '3': 'therapist', 'receptionist': 'reception'}.get(str(d.get('role_id', '')), role) or role
        role = 'reception' if role == 'receptionist' else role
        name = str(d.get('username', '') or d.get('name', '') or '').strip()
        email = str(d.get('email', '') or '').strip().lower()
        errors = {}
        if role not in ('reception', 'therapist'):
            errors['role'] = 'Use "therapist" or "reception". Admins are created through clinic registration.'
        if not name:
            errors['username'] = 'This field is required.'
        from django.core.validators import validate_email
        try:
            validate_email(email)
            if User.all_objects.filter(email__iexact=email).exists():
                errors['email'] = 'An account with this email already exists.'
        except DjangoValidationError:
            errors['email'] = 'Enter a valid email address.'
        if errors:
            return Response(errors, status=400)

        temp_password = _temp_password()
        user = User.objects.create_user(
            email=email, password=temp_password, username=name[:150], role=role,
            clinic_id=request.user.clinic_id, must_change_password=True,
            phone=str(d.get('phone', '') or '')[:30],
            specialist_area=str(d.get('specialist_area', '') or '')[:100],
        )
        data = _format_staff(user, request)
        data.update({'must_change_password': True, 'temp_password': temp_password})
        return Response(data, status=201)


def _temp_password():
    """12 characters, easy to read out loud (no 0/O/1/l/I), always passes the password rules."""
    alphabet = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(12))
        if any(c.isdigit() for c in pwd) and any(c.isupper() for c in pwd) and any(c.islower() for c in pwd):
            return pwd


class ChangePasswordView(APIView):
    """
    POST /api/users/change-password/
    Body: {"new_password": "...", "confirm_password": "...", "current_password": "..."}
    current_password is not needed while must_change_password is true (first login with a temp
    password). Clears must_change_password. Available to every logged-in clinic user.
    """
    throttle_scope = 'otp_verify'

    def post(self, request):
        user = User.all_objects.get(pk=request.user.pk)
        new_password = request.data.get('new_password', '') or ''
        confirm = request.data.get('confirm_password', '') or ''
        if not user.must_change_password:
            if not user.check_password(request.data.get('current_password', '') or ''):
                return Response({'current_password': 'Current password is incorrect.'}, status=400)
        if not new_password or not confirm:
            return Response({'error': 'Both password fields are required.'}, status=400)
        if new_password != confirm:
            return Response({'confirm_password': 'Passwords do not match.'}, status=400)
        if user.check_password(new_password):
            return Response({'new_password': 'Choose a password different from the current one.'}, status=400)
        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return Response({'new_password': ' '.join(e.messages)}, status=400)
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])
        return Response({'message': 'Password updated.', 'must_change_password': False})


class StaffResetPasswordView(APIView):
    """
    POST /api/users/staff/<id>/reset-password/  — admin only, own clinic.
    Issues a new temporary password (returned once) and sets must_change_password again.
    """
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        user = User.objects.filter(pk=pk, role__in=['reception', 'therapist']).first()
        if not user:
            return Response({'error': 'Staff member not found.'}, status=404)
        temp_password = _temp_password()
        user.set_password(temp_password)
        user.must_change_password = True
        user.save(update_fields=['password', 'must_change_password'])
        return Response({'id': user.id, 'email': user.email, 'temp_password': temp_password,
                         'must_change_password': True})


class ForgotPasswordView(APIView):
    """
    POST /api/users/forgot-password/
    Body: {"email": "user@aura.com"}
    Always answers the same way, so it can't be used to discover which emails exist.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope     = 'otp_request'

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email is required'}, status=400)

        user = User.all_objects.filter(email__iexact=email, is_active=True).first()
        if user and cache.add(f'password_reset_wait_{email}', 1, timeout=OTP_RESEND_WAIT):
            otp = f'{secrets.randbelow(1_000_000):06d}'
            cache.set(f'password_reset_otp_{email}', {'otp': otp, 'attempts': 0}, timeout=OTP_TTL)
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
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Password reset email failed')

        return Response({'message': GENERIC_OTP_MSG, 'email': email})


class VerifyOTPView(APIView):
    """
    POST /api/users/verify-otp/
    Body: {"email": "user@aura.com", "otp": "123456"}
    Returns a single-use reset_token (valid 15 minutes) — it cannot be used to call other APIs.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope     = 'otp_verify'

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp   = str(request.data.get('otp', '')).strip()

        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=400)

        key   = f'password_reset_otp_{email}'
        entry = cache.get(key)
        if not entry:
            return Response({'error': 'OTP expired or invalid. Please request a new one.'}, status=400)

        if not hmac.compare_digest(entry['otp'], otp):
            entry['attempts'] += 1
            if entry['attempts'] >= OTP_MAX_ATTEMPTS:
                cache.delete(key)
                return Response({'error': 'Too many wrong attempts. Please request a new OTP.'}, status=400)
            cache.set(key, entry, timeout=OTP_TTL)
            return Response({'error': 'Invalid OTP'}, status=400)

        cache.delete(key)
        user = User.all_objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return Response({'error': 'OTP expired or invalid. Please request a new one.'}, status=400)

        # Tied to the current password hash → stops working once the password changes
        reset_token = signing.dumps({'uid': user.pk, 'ph': user.password[-12:]}, salt=RESET_SALT)
        return Response({'message': 'OTP verified successfully', 'reset_token': reset_token})


class ResetPasswordView(APIView):
    """
    POST /api/users/reset-password/
    Body: {"new_password": "...", "confirm_password": "..."}
    Header: Authorization: Bearer <reset_token>   (or "reset_token" in the body)
    """
    permission_classes     = [permissions.AllowAny]
    authentication_classes = []          # reset_token is not a login token
    throttle_scope         = 'otp_verify'

    def post(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        token  = request.data.get('reset_token') or (header[7:].strip() if header.startswith('Bearer ') else '')
        try:
            data = signing.loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE)
            user = User.all_objects.get(pk=data['uid'], is_active=True)
            if user.password[-12:] != data['ph']:
                raise ValueError('token already used')
        except Exception:
            return Response({'error': 'Reset link is invalid or has expired. Please start again.'}, status=400)

        new_password     = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')
        if not new_password or not confirm_password:
            return Response({'error': 'Both password fields are required'}, status=400)
        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=400)
        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return Response({'error': ' '.join(e.messages)}, status=400)

        user.set_password(new_password)
        user.save()

        # Log out every existing session of this user
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            for t in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=t)
        except Exception:
            pass

        return Response({'message': 'Password reset successfully. Please login again.'})


def _format_staff(user, request=None):
    """Shared helper — returns a consistent staff dict."""
    try:
        from appointments.models import Appointment
        clients_count = Appointment.objects.filter(
            staff=user
        ).values('patient').distinct().count()
    except Exception:
        clients_count = 0

    return {
        'id':                   user.id,
        'username':             user.username or user.email.split('@')[0],
        'email':                user.email,
        'role':                 user.role,
        'role_id':              ROLE_ID_MAP.get(user.role, 1),
        'profile_image':        _safe_image(user.profile_image),
        'phone':                user.phone,
        'specialist_area':      user.specialist_area,
        'joining_date':         user.joining_date,
        'years_of_experience':  user.years_of_experience,
        'rating':               0,
        'clients':              clients_count,
    }


class StaffDetailView(APIView):
    """
    Look up, retrieve, and edit a single staff member by their ID.
    The ID is obtained from StaffSearchView above.

    GET /api/users/staff/<id>/   — retrieve a single staff member
    PUT /api/users/staff/<id>/   — update staff details (all fields optional)

    Body for PUT (all fields optional):
    {
        "username":            "Jane Smith",
        "email":               "jane@auraclinic.com",
        "role_id":             3,              // 1=Admin 2=Receptionist 3=Therapist 4=Client
        "phone":               "+1 (555) 000-0000",
        "specialist_area":     "Medical Aesthetician",
        "joining_date":        "2024-04-24",   // ISO format YYYY-MM-DD
        "years_of_experience": 6
    }
    """
    permission_classes = [IsAdmin]

    def _get_staff_or_404(self, pk):
        try:
            return User.objects.get(pk=pk, role__in=['reception', 'therapist'])
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self._get_staff_or_404(pk)
        if user is None:
            return Response({'error': 'Staff member not found.'}, status=404)
        data = _format_staff(user)
        data.update(_staff_treatments(user))
        return Response(data)

    def _update(self, request, pk):
        user = self._get_staff_or_404(pk)
        if user is None:
            return Response({'error': 'Staff member not found.'}, status=404)

        # Support both JSON and multipart (form-data for image upload)
        serializer = StaffUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            # Handle image file upload — save file and return URL
            image_file = request.FILES.get('profile_image')
            if image_file:
                # Save to MEDIA_ROOT/staff/
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'staff')
                os.makedirs(upload_dir, exist_ok=True)

                from utils.upload_security import checked_ext, random_token
                ext       = checked_ext(image_file, 'image')
                filename  = f"staff_{updated_user.id}_{random_token()}{ext}"
                filepath  = os.path.join(upload_dir, filename)

                with open(filepath, 'wb+') as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)

                # Build absolute URL
                base_url  = request.build_absolute_uri('/')
                image_url = f"{base_url.rstrip('/')}{settings.MEDIA_URL}staff/{filename}"
                updated_user.profile_image = image_url
                updated_user.save()
            data = _format_staff(updated_user)
            data['message'] = 'Staff member updated successfully.'
            return Response(data)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        user = self._get_staff_or_404(pk)
        if user is None:
            return Response({'error': 'Staff member not found.'}, status=404)
        # Deactivate instead of hard delete — blocks login, preserves data
        user.is_active = False
        user.save()
        return Response({'message': f'{user.username or user.email} has been deactivated and can no longer login.'})

def _staff_treatments(user):
    """Treatments assigned to this staff member (own clinic only), by name."""
    treatments = list(user.treatments.order_by('name').values('id', 'name'))
    return {'treatments': treatments, 'treatment_ids': [t['id'] for t in treatments]}


class StaffTreatmentsView(APIView):
    """
    GET   /api/users/staff/<id>/treatments/  → {staff_id, treatments: [{id, name}], treatment_ids}
    PATCH /api/users/staff/<id>/treatments/  {"treatment_ids": [3, 7, 12]}
          Replaces this staff member's full set of treatments (same as editing staff_ids on each
          treatment). [] removes all. Returns the updated staff record.
    """
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        user = _get_staff_member(pk)
        if user is None:
            return Response({'error': 'Staff member not found.'}, status=404)
        return Response({'staff_id': user.id, **_staff_treatments(user)})

    def patch(self, request, pk):
        from django.db import transaction
        from treatments.models import Treatment

        user = _get_staff_member(pk)
        if user is None:
            return Response({'error': 'Staff member not found.'}, status=404)
        raw = request.data.get('treatment_ids') if hasattr(request.data, 'get') else None
        if raw is None:
            return Response({'treatment_ids': 'This field is required (use [] to remove all).'}, status=400)
        if not isinstance(raw, list) or any(isinstance(v, bool) or not str(v).strip().isdigit() for v in raw):
            return Response({'treatment_ids': 'Must be a list of treatment IDs.'}, status=400)
        ids = sorted({int(v) for v in raw})
        found = set(Treatment.objects.filter(id__in=ids).values_list('id', flat=True))
        missing = [i for i in ids if i not in found]
        if missing:
            return Response({'treatment_ids': f'Treatment(s) not found: {missing}.', 'invalid_ids': missing}, status=400)
        with transaction.atomic():
            user.treatments.set(ids)
        data = _format_staff(user)
        data.update(_staff_treatments(user))
        data['message'] = 'Treatments updated.'
        return Response(data)

    def put(self, request, pk):
        return self.patch(request, pk)


# ─── Staff Schedule Views ─────────────────────────────────────────────────────

from .models import StaffWorkingHours, StaffBreakTime, StaffLeave
from .serializers import WorkingHoursSerializer, BreakTimeSerializer, LeaveSerializer


def _get_staff_member(pk):
    """Return staff (reception/therapist) by pk, or None."""
    try:
        return User.objects.get(pk=pk, role__in=['reception', 'therapist'])
    except User.DoesNotExist:
        return None


# ── Working Hours ─────────────────────────────────────────────────────────────

class WorkingHoursListView(APIView):
    """
    GET  /api/users/staff/<staff_id>/working-hours/
         Returns all 7 days. Days with no entry are shown as 'day_off: true'.

    POST /api/users/staff/<staff_id>/working-hours/
         Add a working day.
         Body: { "day": "Mon", "start_time": "09:00", "end_time": "17:00" }
         Day options: Mon Tue Wed Thu Fri Sat Sun
    """
    permission_classes = [IsAdmin]

    DAYS_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    def get(self, request, staff_id):
        staff = _get_staff_member(staff_id)
        if not staff:
            return Response({'error': 'Staff member not found.'}, status=404)

        entries = {wh.day: wh for wh in StaffWorkingHours.objects.filter(staff=staff)}
        days = []
        for day in self.DAYS_ORDER:
            if day in entries:
                wh = entries[day]
                days.append({
                    'id':         wh.id,
                    'day':        day,
                    'start_time': wh.start_time,
                    'end_time':   wh.end_time,
                    'day_off':    False,
                })
            else:
                days.append({'day': day, 'day_off': True, 'is_added': False})

        return Response({
            'is_added': len(entries) > 0,
            'days':     days,
        })

    def post(self, request, staff_id):
        """
        Accepts either a single day or a list of days in one request.

        Single day:
        {
            "day": "Mon", "start_time": "09:00", "end_time": "17:00"
        }

        Bulk (all days at once) — send a list:
        [
            { "day": "Mon", "start_time": "09:00", "end_time": "17:00" },
            { "day": "Tue", "start_time": "09:00", "end_time": "17:00" },
            { "day": "Wed", "day_off": true },
            ...
        ]
        For days with "day_off": true, any existing entry is deleted (sets to day off).
        For working days, existing entries are updated and new ones are created.
        """
        staff = _get_staff_member(staff_id)
        if not staff:
            return Response({'error': 'Staff member not found.'}, status=404)

        data = request.data

        # ── Bulk mode: list of days ──────────────────────────────────────────
        if isinstance(data, list):
            VALID_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            errors  = {}
            results = []

            for item in data:
                day = item.get('day', '')
                if day not in VALID_DAYS:
                    errors[day or 'unknown'] = 'Invalid day. Use Mon Tue Wed Thu Fri Sat Sun.'
                    continue

                # day_off: true — delete the entry if it exists
                if item.get('day_off', False):
                    StaffWorkingHours.objects.filter(staff=staff, day=day).delete()
                    results.append({'day': day, 'day_off': True, 'is_added': False})
                    continue

                # Working day — upsert (update or create)
                existing = StaffWorkingHours.objects.filter(staff=staff, day=day).first()
                serializer = WorkingHoursSerializer(
                    existing if existing else None,
                    data={'day': day, 'start_time': item.get('start_time'), 'end_time': item.get('end_time')},
                    partial=False
                )
                if serializer.is_valid():
                    serializer.save(staff=staff)
                    results.append({**serializer.data, 'day_off': False, 'is_added': True})
                else:
                    errors[day] = serializer.errors

            if errors:
                return Response({'errors': errors, 'saved': results}, status=400)
            total = StaffWorkingHours.objects.filter(staff=staff).count()
            return Response({'is_added': total > 0, 'days': results}, status=201)

        # ── Single day mode ──────────────────────────────────────────────────
        day = data.get('day', '')
        existing = StaffWorkingHours.objects.filter(staff=staff, day=day).first()
        serializer = WorkingHoursSerializer(
            existing if existing else None,
            data=data,
            partial=False
        )
        if serializer.is_valid():
            serializer.save(staff=staff)
            total = StaffWorkingHours.objects.filter(staff=staff).count()
            return Response({'is_added': total > 0, 'days': [serializer.data]}, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, staff_id):
        """
        Bulk update working hours in one request.

        PATCH /api/users/staff/<staff_id>/working-hours/
        [
            { "day": "Mon", "start_time": "09:00", "end_time": "13:00" },
            { "day": "Tue", "day_off": true },
            { "day": "Wed", "start_time": "10:00", "end_time": "18:00" }
        ]

        - Working day: updates if exists, creates if not
        - day_off: true: deletes the entry (sets to day off)
        """
        staff = _get_staff_member(staff_id)
        if not staff:
            return Response({'error': 'Staff member not found.'}, status=404)

        data = request.data
        if not isinstance(data, list):
            return Response({'error': 'Send a list of days.'}, status=400)

        VALID_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        errors  = {}
        results = []

        for item in data:
            day = item.get('day', '')
            if day not in VALID_DAYS:
                errors[day or 'unknown'] = 'Invalid day. Use Mon Tue Wed Thu Fri Sat Sun.'
                continue

            if item.get('day_off', False):
                StaffWorkingHours.objects.filter(staff=staff, day=day).delete()
                results.append({'day': day, 'day_off': True, 'is_added': False})
                continue

            existing = StaffWorkingHours.objects.filter(staff=staff, day=day).first()
            serializer = WorkingHoursSerializer(
                existing if existing else None,
                data={'day': day, 'start_time': item.get('start_time'), 'end_time': item.get('end_time')},
                partial=False
            )
            if serializer.is_valid():
                serializer.save(staff=staff)
                results.append({**serializer.data, 'day_off': False, 'is_added': True})
            else:
                errors[day] = serializer.errors

        if errors:
            return Response({'errors': errors, 'saved': results}, status=400)

        # Return full 7-day schedule after update
        DAYS_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        all_entries = {wh.day: wh for wh in StaffWorkingHours.objects.filter(staff=staff)}
        full_schedule = []
        for day in DAYS_ORDER:
            if day in all_entries:
                wh = all_entries[day]
                full_schedule.append({
                    'id':         wh.id,
                    'day':        day,
                    'start_time': wh.start_time,
                    'end_time':   wh.end_time,
                    'day_off':    False,
                    'is_added':   True,
                })
            else:
                full_schedule.append({'day': day, 'day_off': True, 'is_added': False})
        return Response({'is_added': len(all_entries) > 0, 'days': full_schedule})


class WorkingHoursDetailView(APIView):
    """
    PUT    /api/users/staff/<staff_id>/working-hours/<id>/
           Edit start/end time for a day.
           Body: { "start_time": "10:00", "end_time": "18:00" }

    DELETE /api/users/staff/<staff_id>/working-hours/<id>/
           Mark the day as day off (removes the entry).
    """
    permission_classes = [IsAdmin]

    def _get_entry(self, staff_id, pk):
        try:
            return StaffWorkingHours.objects.get(pk=pk, staff_id=staff_id)
        except StaffWorkingHours.DoesNotExist:
            return None

    def _update(self, request, staff_id, pk):
        if not _get_staff_member(staff_id):
            return Response({'error': 'Staff member not found.'}, status=404)
        entry = self._get_entry(staff_id, pk)
        if not entry:
            return Response({'error': 'Working hours entry not found.'}, status=404)

        serializer = WorkingHoursSerializer(entry, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def put(self, request, staff_id, pk):
        return self._update(request, staff_id, pk)

    def patch(self, request, staff_id, pk):
        return self._update(request, staff_id, pk)

    def delete(self, request, staff_id, pk):
        if not _get_staff_member(staff_id):
            return Response({'error': 'Staff member not found.'}, status=404)
        entry = self._get_entry(staff_id, pk)
        if not entry:
            return Response({'error': 'Working hours entry not found.'}, status=404)

        day = entry.day
        entry.delete()
        return Response({'message': f'{day} set to day off.'})


# ── Break Times ───────────────────────────────────────────────────────────────

class BreakTimeListView(APIView):
    """
    GET  /api/users/staff/<staff_id>/break-times/
         Returns all break times for the staff member.

    POST /api/users/staff/<staff_id>/break-times/
         Add a break time.
         Body: { "start_time": "13:00", "end_time": "14:00", "label": "Lunch" }
         label is optional.
    """
    permission_classes = [IsAdmin]

    def get(self, request, staff_id):
        staff = _get_staff_member(staff_id)
        if not staff:
            return Response({'error': 'Staff member not found.'}, status=404)

        breaks = StaffBreakTime.objects.filter(staff=staff)
        return Response({
            'is_added': breaks.count() > 0,
            'breaks':   BreakTimeSerializer(breaks, many=True).data,
        })

    def post(self, request, staff_id):
        staff = _get_staff_member(staff_id)
        if not staff:
            return Response({'error': 'Staff member not found.'}, status=404)

        serializer = BreakTimeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(staff=staff)
            total = StaffBreakTime.objects.filter(staff=staff).count()
            return Response({
                'is_added': total > 0,
                'breaks':   [serializer.data],
            }, status=201)
        return Response(serializer.errors, status=400)


class BreakTimeDetailView(APIView):
    """
    PUT    /api/users/staff/<staff_id>/break-times/<id>/
           Edit a break time.
           Body: { "start_time": "13:30", "end_time": "14:30", "label": "Prayer" }

    DELETE /api/users/staff/<staff_id>/break-times/<id>/
           Remove a break time.
    """
    permission_classes = [IsAdmin]

    def _get_entry(self, staff_id, pk):
        try:
            return StaffBreakTime.objects.get(pk=pk, staff_id=staff_id)
        except StaffBreakTime.DoesNotExist:
            return None

    def _update(self, request, staff_id, pk):
        if not _get_staff_member(staff_id):
            return Response({'error': 'Staff member not found.'}, status=404)
        entry = self._get_entry(staff_id, pk)
        if not entry:
            return Response({'error': 'Break time not found.'}, status=404)

        serializer = BreakTimeSerializer(entry, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def put(self, request, staff_id, pk):
        return self._update(request, staff_id, pk)

    def patch(self, request, staff_id, pk):
        return self._update(request, staff_id, pk)

    def delete(self, request, staff_id, pk):
        if not _get_staff_member(staff_id):
            return Response({'error': 'Staff member not found.'}, status=404)
        entry = self._get_entry(staff_id, pk)
        if not entry:
            return Response({'error': 'Break time not found.'}, status=404)

        entry.delete()
        return Response({'message': 'Break time deleted.'})


# ── Leaves ────────────────────────────────────────────────────────────────────

LEAVE_STATUSES = ('pending', 'approved', 'rejected')


def _leave_staff(request, staff_id):
    """
    Who may manage whose leave: admin → any therapist/receptionist; therapist → only their own.
    Returns (staff, error_response).
    """
    role = getattr(request.user, 'role', '') or ''
    if role == 'therapist':
        if str(staff_id) != str(request.user.pk):
            return None, Response({'error': 'You can only view or request your own leave.',
                                   'code': 'not_own_records'}, status=403)
    elif role != 'admin':
        return None, Response({'error': 'Only a clinic admin can manage staff leave.', 'code': 'admin_only'}, status=403)
    staff = _get_staff_member(staff_id)
    if not staff:
        return None, Response({'error': 'Staff member not found.'}, status=404)
    return staff, None


def _status_filter(request, qs):
    raw = str(request.query_params.get('status', '') or '').strip()
    if not raw:
        return qs, None
    wanted = [v.strip() for v in raw.split(',') if v.strip()]
    if not wanted or any(v not in LEAVE_STATUSES for v in wanted):
        return None, Response({'status': 'Use pending, approved or rejected (comma-separate for several).'}, status=400)
    return qs.filter(status__in=wanted), None


def _overlap_error(staff, from_date, to_date, exclude_pk=None):
    clash = (StaffLeave.objects.filter(staff=staff, status__in=['pending', 'approved'],
                                       from_date__lte=to_date, to_date__gte=from_date)
             .exclude(pk=exclude_pk).order_by('from_date').first())
    if clash:
        return Response({'from_date': f'Overlaps an existing {clash.status} leave '
                                      f'({clash.from_date} to {clash.to_date}, id {clash.id}).',
                         'code': 'leave_overlap', 'overlapping_leave_id': clash.id}, status=400)
    return None


def _appointments_during(leave):
    """Booked (not cancelled) appointments inside an approved leave, so the admin can rebook them."""
    from appointments.models import Appointment
    rows = (Appointment.objects.filter(staff=leave.staff, date_time__date__gte=leave.from_date,
                                       date_time__date__lte=leave.to_date)
            .exclude(status='cancelled').select_related('patient').order_by('date_time'))
    return [{'appointment_id': a.id, 'date_time': a.date_time,
             'patient_name': a.patient.name if a.patient else None, 'status': a.status} for a in rows]


def _leave_response(leave, status_code=200):
    data = LeaveSerializer(leave).data
    if leave.status == 'approved':
        data['appointments_during_leave'] = _appointments_during(leave)
    return Response(data, status=status_code)


def _apply_review(leave, new_status, user, note=None):
    leave.status = new_status
    if new_status == 'pending':
        leave.reviewed_by, leave.reviewed_at, leave.review_note = None, None, ''
    else:
        leave.reviewed_by, leave.reviewed_at = user, timezone.now()
        if note is not None:
            leave.review_note = str(note)[:255]


class LeaveListView(APIView):
    """
    GET  /api/users/staff/<staff_id>/leaves/?status=pending      (admin: any staff · therapist: own)
         status filter optional, comma-separate for several.

    POST /api/users/staff/<staff_id>/leaves/
         Body: { "from_date": "2026-04-23", "to_date": "2026-04-24", "reason": "Sick" }
         admin     → approved straight away (or send "status": "pending" | "rejected")
         therapist → own staff_id only, always created as "pending" for an admin to review
    Only approved leave blocks the schedule / booking.
    """
    permission_classes = [IsClinicStaff]

    def get(self, request, staff_id):
        staff, error = _leave_staff(request, staff_id)
        if error:
            return error
        leaves, error = _status_filter(request, StaffLeave.objects.filter(staff=staff)
                                       .select_related('staff', 'reviewed_by').order_by('-from_date', '-id'))
        if error:
            return error
        return Response(LeaveSerializer(leaves, many=True).data)

    def post(self, request, staff_id):
        staff, error = _leave_staff(request, staff_id)
        if error:
            return error
        serializer = LeaveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        is_admin = request.user.role == 'admin'
        new_status = 'pending'
        if is_admin:
            new_status = request.data.get('status') or 'approved'
            if new_status not in LEAVE_STATUSES:
                return Response({'status': 'Use pending, approved or rejected.'}, status=400)
        d = serializer.validated_data
        if new_status != 'rejected':
            overlap = _overlap_error(staff, d['from_date'], d['to_date'])
            if overlap:
                return overlap
        leave = StaffLeave(staff=staff, created_by=request.user, **d)
        _apply_review(leave, new_status, request.user, request.data.get('review_note') if is_admin else None)
        leave.save()
        return _leave_response(leave, 201)


class LeaveReviewListView(APIView):
    """
    GET /api/users/leaves/?status=pending&staff_id=8&page=1&page_size=20   (admin)
    Leave across all staff: the admin's review inbox. Pending requests first, then by start date.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        from django.db.models import Case, IntegerField, Value, When
        qs = StaffLeave.objects.select_related('staff', 'reviewed_by').filter(
            staff__role__in=['reception', 'therapist'])
        raw_staff = str(request.query_params.get('staff_id', '') or '').strip()
        if raw_staff:
            if not raw_staff.isdigit():
                return Response({'staff_id': 'Must be a staff id.'}, status=400)
            qs = qs.filter(staff_id=int(raw_staff))
        qs, error = _status_filter(request, qs)
        if error:
            return error
        qs = qs.annotate(_pending_first=Case(When(status='pending', then=Value(0)), default=Value(1),
                                             output_field=IntegerField())).order_by('_pending_first', 'from_date', 'id')
        from utils.pagination import paginate
        return paginate(request, qs, lambda rows: LeaveSerializer(rows, many=True).data)


class LeaveDetailView(APIView):
    """
    GET    /api/users/staff/<staff_id>/leaves/<id>/
    PATCH  /api/users/staff/<staff_id>/leaves/<id>/     (PUT works the same)
           admin:     any of from_date, to_date, reason, and "status": "approved" | "rejected" | "pending",
                      "review_note": "…" (optional, shown to the therapist)
           therapist: own *pending* request only (from_date, to_date, reason). Can't change status.
    DELETE /api/users/staff/<staff_id>/leaves/<id>/
           admin: any · therapist: withdraw own pending request
    """
    permission_classes = [IsClinicStaff]

    def _get_entry(self, request, staff_id, pk):
        staff, error = _leave_staff(request, staff_id)
        if error:
            return None, error
        entry = StaffLeave.objects.select_related('staff', 'reviewed_by').filter(pk=pk, staff=staff).first()
        if not entry:
            return None, Response({'error': 'Leave record not found.'}, status=404)
        return entry, None

    @staticmethod
    def _therapist_locked(request, entry):
        if request.user.role == 'therapist' and entry.status != 'pending':
            return Response({'error': 'This leave has already been reviewed, so it can no longer be changed. '
                                      'Ask your clinic admin.', 'code': 'leave_already_reviewed'}, status=403)
        return None

    def get(self, request, staff_id, pk):
        entry, error = self._get_entry(request, staff_id, pk)
        return error or _leave_response(entry)

    def _update(self, request, staff_id, pk):
        entry, error = self._get_entry(request, staff_id, pk)
        if error:
            return error
        is_admin = request.user.role == 'admin'
        if not is_admin and ('status' in request.data or 'review_note' in request.data):
            return Response({'error': 'Only a clinic admin can approve or reject leave.', 'code': 'admin_only'}, status=403)
        locked = self._therapist_locked(request, entry)
        if locked:
            return locked
        serializer = LeaveSerializer(entry, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        new_status = request.data.get('status', entry.status) if is_admin else entry.status
        if new_status not in LEAVE_STATUSES:
            return Response({'status': 'Use pending, approved or rejected.'}, status=400)
        d = serializer.validated_data
        from_date, to_date = d.get('from_date', entry.from_date), d.get('to_date', entry.to_date)
        if from_date > to_date:
            return Response({'non_field_errors': ['from_date must be on or before to_date.']}, status=400)
        if new_status != 'rejected':
            overlap = _overlap_error(entry.staff, from_date, to_date, exclude_pk=entry.pk)
            if overlap:
                return overlap
        for field, value in d.items():
            setattr(entry, field, value)
        if is_admin and 'status' in request.data and new_status != entry.status:
            _apply_review(entry, new_status, request.user, request.data.get('review_note'))
        elif is_admin and 'review_note' in request.data:
            entry.review_note = str(request.data.get('review_note') or '')[:255]
        entry.save()
        return _leave_response(entry)

    def put(self, request, staff_id, pk):
        return self._update(request, staff_id, pk)

    def patch(self, request, staff_id, pk):
        return self._update(request, staff_id, pk)

    def delete(self, request, staff_id, pk):
        entry, error = self._get_entry(request, staff_id, pk)
        if error:
            return error
        locked = self._therapist_locked(request, entry)
        if locked:
            return locked
        entry.delete()
        return Response({'message': 'Leave deleted.'})
