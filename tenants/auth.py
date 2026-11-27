"""
Authentication for the two kinds of callers:

- Clinic users (admin / reception / therapist): normal JWT. After the token is checked we
  load the user's clinic, refuse suspended clinics and accounts without a clinic, enforce
  must_change_password, and set the request's clinic so every query is scoped to it.
- Platform Super Admin: separate signed token, separate table, never scoped to a clinic.
"""
from django.core import signing
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

from .context import set_current_clinic_id, set_current_user

PLATFORM_TOKEN_SALT = 'aura-platform-admin'
PLATFORM_TOKEN_MAX_AGE = 12 * 60 * 60          # 12 hours

# Paths a user who still has a temporary password may call
PASSWORD_CHANGE_ALLOWED = (
    '/api/users/change-password/',
    '/api/users/me/',
    '/api/users/logout/',
)


# Paths a clinic blocked for billing (trial ended / unpaid / canceled) may still call
BILLING_ALLOWED = (
    '/api/billing/',
    '/api/users/me/',
    '/api/users/logout/',
    '/api/users/change-password/',
)


class BillingBlocked(exceptions.APIException):
    status_code = 403
    default_code = 'billing_blocked'

    def __init__(self, code):
        from .billing import BLOCK_MESSAGES
        super().__init__({'error': BLOCK_MESSAGES[code], 'code': code}, code)


class ClinicSuspended(exceptions.APIException):
    status_code = 403
    default_code = 'clinic_suspended'
    default_detail = {'error': 'Your clinic account is suspended. Please contact support.', 'code': 'clinic_suspended'}


class NoClinic(exceptions.APIException):
    status_code = 403
    default_code = 'no_clinic'
    default_detail = {'error': 'This account is not linked to a clinic.', 'code': 'no_clinic'}


class PasswordChangeRequired(exceptions.APIException):
    status_code = 403
    default_code = 'password_change_required'
    default_detail = {'error': 'Please set a new password before continuing.', 'code': 'password_change_required'}


def check_clinic_user(user, path=None):
    """Shared by login, token refresh and every authenticated request."""
    clinic = getattr(user, 'clinic', None)
    if clinic is None:
        raise NoClinic()
    if clinic.status != 'active':
        raise ClinicSuspended()
    if path is not None and getattr(user, 'must_change_password', False) and not path.startswith(PASSWORD_CHANGE_ALLOWED):
        raise PasswordChangeRequired()
    if path is not None:
        # Billing is enforced per request, not at login: a blocked clinic can still log in
        # and reach the billing screen to add a card.
        from .billing import billing_state, refresh_trial_status
        refresh_trial_status(clinic)
        _, block, _ = billing_state(clinic)
        if block and not path.startswith(BILLING_ALLOWED):
            raise BillingBlocked(block)
    return clinic


def _checked(request, user):
    try:
        return check_clinic_user(user, request.path)
    except exceptions.APIException:
        # lets the access log name the user even though authentication stopped here
        request._request.denied_user = user
        raise


class TenantJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, token = result
        clinic = _checked(request, user)
        set_current_clinic_id(clinic.id)
        set_current_user(user)
        return user, token


class TenantSessionAuthentication(SessionAuthentication):
    """Browsable API / session logins get the same clinic scoping."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, auth = result
        clinic = _checked(request, user)
        set_current_clinic_id(clinic.id)
        set_current_user(user)
        return user, auth


# ── Aura Console (platform users) ─────────────────────────────────────────────

# Paths a console user with a temporary password may call
PLATFORM_PASSWORD_CHANGE_ALLOWED = (
    '/api/platform/change-password/',
    '/api/platform/me/',
    '/api/platform/logout/',
)


def make_platform_token(admin):
    """
    Signed, 12-hour token. `ph` (end of the password hash) ends every session when the password
    changes; `jti` lets one session be ended on its own by logout.
    """
    import secrets
    return signing.dumps({'pa': admin.pk, 'ph': admin.password[-12:], 'jti': secrets.token_hex(16)},
                         salt=PLATFORM_TOKEN_SALT)


def read_platform_token(token):
    """Returns the token payload, or raises AuthenticationFailed."""
    try:
        return signing.loads(token, salt=PLATFORM_TOKEN_SALT, max_age=PLATFORM_TOKEN_MAX_AGE)
    except signing.SignatureExpired:
        raise exceptions.AuthenticationFailed({'error': 'Session expired. Please log in again.', 'code': 'token_expired'})
    except signing.BadSignature:
        raise exceptions.AuthenticationFailed({'error': 'Invalid console session. Please log in again.',
                                               'code': 'token_not_valid'})


def revoke_platform_token(data):
    import datetime
    from .models import PlatformRevokedToken
    jti = data.get('jti')
    if not jti:
        return
    now = timezone.now()
    PlatformRevokedToken.objects.filter(expires_at__lt=now).delete()
    PlatformRevokedToken.objects.get_or_create(
        jti=jti, defaults={'expires_at': now + datetime.timedelta(seconds=PLATFORM_TOKEN_MAX_AGE)})


class PlatformAdminAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith(self.keyword + ' '):
            return None
        token = header[len(self.keyword) + 1:].strip()
        data = read_platform_token(token)
        from .models import PlatformAdmin, PlatformRevokedToken
        admin = PlatformAdmin.objects.filter(pk=data.get('pa'), is_active=True).first()
        if not admin or admin.password[-12:] != data.get('ph'):
            raise exceptions.AuthenticationFailed({'error': 'Your console session has ended. Please log in again.',
                                                   'code': 'session_ended'})
        if data.get('jti') and PlatformRevokedToken.objects.filter(jti=data['jti']).exists():
            raise exceptions.AuthenticationFailed({'error': 'You have logged out. Please log in again.',
                                                   'code': 'session_ended'})
        if admin.must_change_password and not request.path.startswith(PLATFORM_PASSWORD_CHANGE_ALLOWED):
            raise PasswordChangeRequired()
        admin.is_authenticated = True
        request.platform_token_data = data
        return admin, token

    def authenticate_header(self, request):
        return self.keyword


class ReadOnlyRole(exceptions.APIException):
    status_code = 403
    default_code = 'read_only_role'
    default_detail = {'error': 'Your console role (Viewer) is read-only.', 'code': 'read_only_role'}


class IsPlatformAdmin(BasePermission):
    """Any console user may read; only a Super Admin may change anything."""
    def has_permission(self, request, view):
        from rest_framework.permissions import SAFE_METHODS
        from .models import PlatformAdmin
        if not isinstance(request.user, PlatformAdmin):
            return False
        if request.method not in SAFE_METHODS and request.user.role != 'super_admin':
            raise ReadOnlyRole()
        return True


class IsPlatformUser(BasePermission):
    """Any logged-in console user, whatever the method (own session / own password)."""
    def has_permission(self, request, view):
        from .models import PlatformAdmin
        return isinstance(request.user, PlatformAdmin)
