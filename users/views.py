from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from users.permissions import IsAdmin
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, StaffUpdateSerializer
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
            # Match name (startswith) OR email (startswith) — for live search as user types
            users = users.filter(
                Q(username__istartswith=search) |
                Q(email__istartswith=search)
            )

        result = []
        for u in users:
            result.append(_format_staff(u))
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


def _format_staff(user, request=None):
    """Shared helper — returns a consistent staff dict."""
    image_url = user.profile_image if user.profile_image else None

    return {
        'id':                   user.id,
        'username':             user.username or user.email.split('@')[0],
        'email':                user.email,
        'role':                 user.role,
        'role_id':              ROLE_ID_MAP.get(user.role, 1),
        'profile_image':        image_url,
        'phone':                user.phone,
        'specialist_area':      user.specialist_area,
        'joining_date':         user.joining_date,
        'years_of_experience':  user.years_of_experience,
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
        return Response(_format_staff(user))

    def _update(self, request, pk):
        user = self._get_staff_or_404(pk)
        if user is None:
            return Response({'error': 'Staff member not found.'}, status=404)

        # Support both JSON and multipart (form-data for image upload)
        serializer = StaffUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            # Handle image file upload
            image_file = request.FILES.get('profile_image')
            if image_file:
                import base64, os
                ext       = os.path.splitext(image_file.name)[1].lower()
                image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
                updated_user.profile_image = f"data:image/{ext.strip('.')};base64,{image_b64}"
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
        user.delete()
        return Response({'message': 'Staff member deleted successfully.'})

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

class LeaveListView(APIView):
    """
    GET  /api/users/staff/<staff_id>/leaves/
         Returns all leave records for the staff member.

    POST /api/users/staff/<staff_id>/leaves/
         Add a leave.
         Body: { "from_date": "2026-04-23", "to_date": "2026-04-24", "reason": "Sick" }
         reason is optional.
    """
    permission_classes = [IsAdmin]

    def get(self, request, staff_id):
        staff = _get_staff_member(staff_id)
        if not staff:
            return Response({'error': 'Staff member not found.'}, status=404)

        leaves = StaffLeave.objects.filter(staff=staff)
        return Response(LeaveSerializer(leaves, many=True).data)

    def post(self, request, staff_id):
        staff = _get_staff_member(staff_id)
        if not staff:
            return Response({'error': 'Staff member not found.'}, status=404)

        serializer = LeaveSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(staff=staff)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class LeaveDetailView(APIView):
    """
    PUT    /api/users/staff/<staff_id>/leaves/<id>/
           Edit a leave record.
           Body: { "from_date": "2026-04-25", "to_date": "2026-04-26", "reason": "Holiday" }

    DELETE /api/users/staff/<staff_id>/leaves/<id>/
           Delete a leave record.
    """
    permission_classes = [IsAdmin]

    def _get_entry(self, staff_id, pk):
        try:
            return StaffLeave.objects.get(pk=pk, staff_id=staff_id)
        except StaffLeave.DoesNotExist:
            return None

    def _update(self, request, staff_id, pk):
        if not _get_staff_member(staff_id):
            return Response({'error': 'Staff member not found.'}, status=404)
        entry = self._get_entry(staff_id, pk)
        if not entry:
            return Response({'error': 'Leave record not found.'}, status=404)

        serializer = LeaveSerializer(entry, data=request.data, partial=True)
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
            return Response({'error': 'Leave record not found.'}, status=404)

        entry.delete()
        return Response({'message': 'Leave deleted.'})