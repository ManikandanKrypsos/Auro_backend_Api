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
from . import billing as b
from .models import Clinic, Plan, PlatformAdmin


# ── Clinic registration (public) ──────────────────────────────────────────────

class ClinicRegisterView(APIView):
    """
    POST /api/clinics/register/
    {clinic_name, admin_name, admin_email, admin_password, admin_phone?, plan_id?}
    Creates a new clinic (on a free trial, no card needed) and its first admin, and logs the admin in.
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
        plan = b.default_plan()
        raw_plan = d.get('plan_id')
        if raw_plan not in (None, ''):
            plan = Plan.objects.filter(pk=raw_plan, is_active=True).first() if str(raw_plan).isdigit() else None
            if plan is None:
                errors['plan_id'] = 'Plan not found.'
        if errors:
            return Response(errors, status=400)

        with transaction.atomic():
            clinic = Clinic.objects.create(name=clinic_name[:150], plan=plan,
                                           subscription_status='trialing', trial_end=b.new_trial_end())
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
    status, block, warning = b.billing_state(clinic)
    data.update({
        'plan':                   b.serialize_plan(clinic.plan),
        'subscription_status':    status,
        'trial_end':              clinic.trial_end,
        'current_period_end':     clinic.current_period_end,
        'grace_until':            clinic.grace_until if status == 'past_due' else None,
        'access_blocked':         block is not None or clinic.status != 'active',
        'has_payment_method':     bool(clinic.card_last4),
        'stripe_customer_id':     clinic.stripe_customer_id or None,
        'stripe_subscription_id': clinic.stripe_subscription_id or None,
    })
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
    """GET /api/platform/clinics/?status=active|suspended&subscription_status=&plan_id=&search=  — every clinic."""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        qs = Clinic.objects.select_related('plan').annotate(
            staff_count=Count('users', filter=Q(users__is_active=True), distinct=True),
        )
        status = request.query_params.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        sub_status = request.query_params.get('subscription_status', '').strip()
        plan_id = request.query_params.get('plan_id', '').strip()
        if plan_id.isdigit():
            qs = qs.filter(plan_id=int(plan_id))
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(users__email__icontains=search, users__role='admin')).distinct()
        clinics = [b.refresh_trial_status(c) for c in qs]
        if sub_status:
            clinics = [c for c in clinics if b.billing_state(c)[0] == sub_status]
        admins = _first_admins([c.id for c in clinics])
        return Response([serialize_clinic(c, admins.get(c.id), {'staff_count': c.staff_count}) for c in clinics])


class PlatformClinicDetailView(APIView):
    """GET /api/platform/clinics/<id>/"""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request, pk):
        from users.models import User
        from patients.models import Patient
        clinic = Clinic.objects.select_related('plan').filter(pk=pk).first()
        if not clinic:
            return Response({'error': 'Clinic not found.'}, status=404)
        b.refresh_trial_status(clinic)
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


class PlatformClinicBillingView(APIView):
    """
    PATCH /api/platform/clinics/<id>/billing/   {"plan_id": 2?, "trial_end": "2026-12-31"?, "subscription_status": "active"?}
    Manual overrides for the Super Admin: change plan label, extend a trial, or mark a clinic active
    (e.g. an invoiced customer). Does not touch Stripe — changes in Stripe still arrive via the webhook.
    """
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def patch(self, request, pk):
        import datetime
        clinic = Clinic.objects.select_related('plan').filter(pk=pk).first()
        if not clinic:
            return Response({'error': 'Clinic not found.'}, status=404)
        d = request.data
        if d.get('plan_id') not in (None, ''):
            plan = Plan.objects.filter(pk=d.get('plan_id')).first() if str(d.get('plan_id')).isdigit() else None
            if plan is None:
                return Response({'plan_id': 'Plan not found.'}, status=400)
            clinic.plan = plan
        if d.get('trial_end') not in (None, ''):
            try:
                day = datetime.date.fromisoformat(str(d.get('trial_end'))[:10])
            except ValueError:
                return Response({'trial_end': 'Use YYYY-MM-DD.'}, status=400)
            clinic.trial_end = timezone.make_aware(datetime.datetime.combine(day, datetime.time(23, 59, 59)))
            if clinic.subscription_status == 'trial_expired' and clinic.trial_end > timezone.now():
                clinic.subscription_status = 'trialing'
        if d.get('subscription_status') not in (None, ''):
            new = d.get('subscription_status')
            if new not in dict(Clinic.SUBSCRIPTION_CHOICES):
                return Response({'subscription_status': 'Use trialing, active, past_due, canceled or trial_expired.'}, status=400)
            if new == 'active':
                b.set_active(clinic)
            elif new == 'past_due':
                b.set_past_due(clinic)
            else:
                clinic.subscription_status = new
                if new == 'trialing' and not clinic.trial_end:
                    clinic.trial_end = b.new_trial_end()
        clinic.save()
        return Response(serialize_clinic(clinic, _first_admins([clinic.id]).get(clinic.id)))


# ── Plans (Super Admin) ───────────────────────────────────────────────────────

def _plan_admin(plan):
    data = b.serialize_plan(plan)
    data.update({'stripe_price_id': plan.stripe_price_id, 'is_active': plan.is_active,
                 'clinic_count': getattr(plan, 'clinic_count', None)})
    return data


def _apply_plan(plan, d, creating):
    from decimal import Decimal, InvalidOperation
    errors = {}
    if creating or 'name' in d:
        name = str(d.get('name', '') or '').strip()
        if not name:
            errors['name'] = 'This field is required.'
        plan.name = name[:80]
    if creating or 'price' in d:
        try:
            plan.price = Decimal(str(d.get('price'))).quantize(Decimal('0.01'))
            if plan.price < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError, TypeError):
            errors['price'] = 'Must be a number of 0 or more.'
    if 'currency' in d:
        plan.currency = str(d.get('currency') or 'eur').lower()[:3]
    if 'interval' in d:
        if d.get('interval') not in ('month', 'year'):
            errors['interval'] = 'Use "month" or "year".'
        plan.interval = d.get('interval')
    if 'stripe_price_id' in d:
        plan.stripe_price_id = str(d.get('stripe_price_id') or '').strip()[:100]
    if 'limits' in d:
        if not isinstance(d.get('limits'), dict):
            errors['limits'] = 'Must be an object.'
        plan.limits = d.get('limits') or {}
    if 'is_active' in d:
        plan.is_active = bool(d.get('is_active'))
    return errors


class PlatformPlanListView(APIView):
    """GET /api/platform/plans/  ·  POST /api/platform/plans/ {name, price, currency?, interval?, stripe_price_id?, limits?}"""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        return Response([_plan_admin(p) for p in Plan.objects.annotate(clinic_count=Count('clinics')).order_by('price', 'id')])

    def post(self, request):
        plan = Plan()
        errors = _apply_plan(plan, request.data, creating=True)
        if errors:
            return Response(errors, status=400)
        plan.save()
        plan.clinic_count = 0
        return Response(_plan_admin(plan), status=201)


class PlatformPlanDetailView(APIView):
    """PATCH /api/platform/plans/<id>/  — any of the fields above."""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def patch(self, request, pk):
        plan = Plan.objects.annotate(clinic_count=Count('clinics')).filter(pk=pk).first()
        if not plan:
            return Response({'error': 'Plan not found.'}, status=404)
        errors = _apply_plan(plan, request.data, creating=False)
        if errors:
            return Response(errors, status=400)
        plan.save()
        return Response(_plan_admin(plan))
