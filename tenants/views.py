from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import IsPlatformAdmin, PlatformAdminAuthentication, make_platform_token
from .models import Clinic, PlatformAdmin


# ── Clinic registration (public) ──────────────────────────────────────────────

class ClinicRegisterView(APIView):
    """
    POST /api/clinics/register/
    {clinic_name, admin_name, admin_email, admin_password, admin_phone?}
    Creates a new clinic and its first admin in one step, and logs the admin in.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'auth'

    def post(self, request):
        from users.models import User
        from users.views import auth_payload

        d = request.data
        clinic_name = str(d.get('clinic_name', '') or '').strip()
        admin_name = str(d.get('admin_name', '') or '').strip()
        email = str(d.get('admin_email', '') or '').strip().lower()
        password = str(d.get('admin_password', '') or '')
        errors = {}
        if not clinic_name:
            errors['clinic_name'] = 'This field is required.'
        if not admin_name:
            errors['admin_name'] = 'This field is required.'
        try:
            validate_email(email)
            if User.all_objects.filter(email__iexact=email).exists():
                errors['admin_email'] = 'An account with this email already exists.'
        except DjangoValidationError:
            errors['admin_email'] = 'Enter a valid email address.'
        if not password:
            errors['admin_password'] = 'This field is required.'
        else:
            try:
                validate_password(password, User(email=email, username=admin_name))
            except DjangoValidationError as e:
                errors['admin_password'] = ' '.join(e.messages)
        if errors:
            return Response(errors, status=400)

        with transaction.atomic():
            clinic = Clinic.objects.create(name=clinic_name[:150])
            user = User.all_objects.create_user(
                email=email, password=password, username=admin_name[:150], role='admin',
                clinic=clinic, phone=str(d.get('admin_phone', '') or '')[:30],
            )
        return Response(auth_payload(user), status=201)


# ── Platform Super Admin ──────────────────────────────────────────────────────

def serialize_clinic(clinic, admin=None, counts=None):
    data = {
        'id':               clinic.id,
        'name':             clinic.name,
        'status':           clinic.status,
        'suspended_at':     clinic.suspended_at,
        'suspended_reason': clinic.suspended_reason or None,
        'created_at':       clinic.created_at,
        'admin': {
            'id':    admin.id,
            'name':  admin.username,
            'email': admin.email,
            'phone': admin.phone,
        } if admin else None,
    }
    if counts:
        data.update(counts)
    return data


def _first_admins(clinic_ids):
    from users.models import User
    admins = {}
    for u in User.all_objects.filter(clinic_id__in=clinic_ids, role='admin').order_by('id'):
        admins.setdefault(u.clinic_id, u)
    return admins


class PlatformLoginView(APIView):
    """POST /api/platform/login/  {email, password} → Super Admin token (valid 12 hours)."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'auth'

    def post(self, request):
        email = str(request.data.get('email', '') or '').strip().lower()
        admin = PlatformAdmin.objects.filter(email__iexact=email, is_active=True).first()
        if not admin or not admin.check_password(str(request.data.get('password', '') or '')):
            return Response({'error': 'Invalid email or password.'}, status=400)
        admin.last_login = timezone.now()
        admin.save(update_fields=['last_login'])
        return Response({
            'token': make_platform_token(admin),
            'expires_in': 12 * 60 * 60,
            'admin': {'id': admin.id, 'name': admin.name, 'email': admin.email},
        })


class PlatformMeView(APIView):
    """GET /api/platform/me/"""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        a = request.user
        return Response({'id': a.id, 'name': a.name, 'email': a.email})


class PlatformClinicListView(APIView):
    """GET /api/platform/clinics/?status=active|suspended&search=  — every clinic on the platform."""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        qs = Clinic.objects.annotate(
            staff_count=Count('users', filter=Q(users__is_active=True), distinct=True),
        )
        status = request.query_params.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(users__email__icontains=search, users__role='admin')).distinct()
        clinics = list(qs)
        admins = _first_admins([c.id for c in clinics])
        return Response([serialize_clinic(c, admins.get(c.id), {'staff_count': c.staff_count}) for c in clinics])


class PlatformClinicDetailView(APIView):
    """GET /api/platform/clinics/<id>/"""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request, pk):
        from users.models import User
        from patients.models import Patient
        clinic = Clinic.objects.filter(pk=pk).first()
        if not clinic:
            return Response({'error': 'Clinic not found.'}, status=404)
        users = User.all_objects.filter(clinic=clinic)
        counts = {
            'staff_count':   users.filter(is_active=True).count(),
            'admin_count':   users.filter(role='admin', is_active=True).count(),
            'patient_count': Patient.objects.filter(clinic=clinic).count(),
        }
        return Response(serialize_clinic(clinic, _first_admins([clinic.id]).get(clinic.id), counts))


class PlatformClinicStatusView(APIView):
    """
    POST /api/platform/clinics/<id>/status/  {"status": "active" | "suspended", "reason": "…"}
    A suspended clinic's users can't log in, refresh tokens or call any API until reactivated.
    """
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        clinic = Clinic.objects.filter(pk=pk).first()
        if not clinic:
            return Response({'error': 'Clinic not found.'}, status=404)
        status = request.data.get('status')
        if status not in ('active', 'suspended'):
            return Response({'status': 'Use "active" or "suspended".'}, status=400)
        clinic.status = status
        if status == 'suspended':
            clinic.suspended_at = timezone.now()
            clinic.suspended_reason = str(request.data.get('reason', '') or '')[:255]
        else:
            clinic.suspended_at = None
            clinic.suspended_reason = ''
        clinic.save()
        return Response(serialize_clinic(clinic, _first_admins([clinic.id]).get(clinic.id)))
