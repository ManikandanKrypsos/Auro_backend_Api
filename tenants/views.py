from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import IsPlatformAdmin, IsPlatformUser, PlatformAdminAuthentication, make_platform_token
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


def serialize_platform_user(a, include_admin_fields=True):
    data = {
        'id':                   a.id,
        'name':                 a.name,
        'email':                a.email,
        'role':                 a.role,
        'must_change_password': a.must_change_password,
    }
    if include_admin_fields:
        data.update({
            'status':     a.status,          # invited | active | deactivated
            'is_active':  a.is_active,
            'last_login': a.last_login,
            'created_at': a.created_at,
            'invited_by': {'id': a.invited_by.id, 'name': a.invited_by.name, 'email': a.invited_by.email}
                          if a.invited_by_id and a.invited_by else None,
        })
    return data


def _platform_login_payload(admin):
    return {
        'token':                make_platform_token(admin),
        'expires_in':           12 * 60 * 60,
        'role':                 admin.role,
        'must_change_password': admin.must_change_password,
        'admin':                serialize_platform_user(admin, include_admin_fields=False),
    }


class PlatformLoginView(APIView):
    """POST /api/platform/login/  {email, password} → console token (valid 12 hours) + role."""
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
        return Response(_platform_login_payload(admin))


class PlatformMeView(APIView):
    """GET /api/platform/me/"""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformUser]

    def get(self, request):
        return Response(serialize_platform_user(request.user, include_admin_fields=False))


class PlatformLogoutView(APIView):
    """POST /api/platform/logout/  — ends this session's token on the server straight away."""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformUser]

    def post(self, request):
        from .auth import revoke_platform_token
        revoke_platform_token(getattr(request, 'platform_token_data', {}) or {})
        return Response({'message': 'Logged out.'})


class PlatformChangePasswordView(APIView):
    """
    POST /api/platform/change-password/  {new_password, confirm_password, current_password?}
    current_password isn't needed on first login (temporary password). Every other session of this
    user ends; the response carries a fresh token for this one.
    """
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformUser]
    throttle_scope = 'otp_verify'

    def post(self, request):
        admin = PlatformAdmin.objects.get(pk=request.user.pk)
        new_password = str(request.data.get('new_password', '') or '')
        confirm = str(request.data.get('confirm_password', '') or '')
        if not admin.must_change_password and not admin.check_password(str(request.data.get('current_password', '') or '')):
            return Response({'current_password': 'Current password is incorrect.'}, status=400)
        if not new_password or not confirm:
            return Response({'error': 'Both password fields are required.'}, status=400)
        if new_password != confirm:
            return Response({'confirm_password': 'Passwords do not match.'}, status=400)
        if admin.check_password(new_password):
            return Response({'new_password': 'Choose a password different from the current one.'}, status=400)
        try:
            validate_password(new_password)
        except DjangoValidationError as e:
            return Response({'new_password': ' '.join(e.messages)}, status=400)
        admin.set_password(new_password)
        admin.must_change_password = False
        admin.save(update_fields=['password', 'must_change_password'])
        data = _platform_login_payload(admin)
        data['message'] = 'Password updated.'
        return Response(data)


# ── Console users (invite / list / role / remove) ─────────────────────────────

def _temp_password():
    from users.views import _temp_password as make
    return make()


def _last_super_admin(admin):
    return (admin.role == 'super_admin' and admin.is_active and
            not PlatformAdmin.objects.filter(role='super_admin', is_active=True).exclude(pk=admin.pk).exists())


class PlatformUserListView(APIView):
    """
    GET  /api/platform/users/?role=viewer&status=invited|active|deactivated&search=&page=1&page_size=20
    POST /api/platform/users/  {email, role: "super_admin" | "viewer", name?}  (Super Admin)
         → the new user + temp_password (shown once); they must set their own password on first login.
    """
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        qs = PlatformAdmin.objects.select_related('invited_by').order_by('-is_active', 'name', 'id')
        p = request.query_params
        if p.get('role'):
            if p['role'] not in dict(PlatformAdmin.ROLE_CHOICES):
                return Response({'role': 'Use super_admin or viewer.'}, status=400)
            qs = qs.filter(role=p['role'])
        status = p.get('status', '').strip()
        if status:
            filters = {'deactivated': Q(is_active=False), 'invited': Q(is_active=True, must_change_password=True),
                       'active': Q(is_active=True, must_change_password=False)}
            if status not in filters:
                return Response({'status': 'Use invited, active or deactivated.'}, status=400)
            qs = qs.filter(filters[status])
        search = p.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
        from utils.pagination import paginate
        return paginate(request, qs, lambda rows: [serialize_platform_user(a) for a in rows])

    def post(self, request):
        d = request.data
        email = str(d.get('email', '') or '').strip().lower()
        role = str(d.get('role', '') or '').strip()
        name = str(d.get('name', '') or '').strip() or email.split('@')[0]
        errors = {}
        try:
            validate_email(email)
            if PlatformAdmin.objects.filter(email__iexact=email).exists():
                errors['email'] = 'A console user with this email already exists.'
        except DjangoValidationError:
            errors['email'] = 'Enter a valid email address.'
        if role not in dict(PlatformAdmin.ROLE_CHOICES):
            errors['role'] = 'Use super_admin or viewer.'
        if errors:
            return Response(errors, status=400)
        temp_password = _temp_password()
        admin = PlatformAdmin(name=name[:150], email=email, role=role, must_change_password=True,
                              invited_by=request.user)
        admin.set_password(temp_password)
        admin.save()
        data = serialize_platform_user(admin)
        data['temp_password'] = temp_password
        return Response(data, status=201)


class PlatformUserDetailView(APIView):
    """
    GET    /api/platform/users/<id>/
    PATCH  /api/platform/users/<id>/  {role?, name?, is_active?}   (Super Admin)
    DELETE /api/platform/users/<id>/  — deactivates: can't log in, current sessions end at once.
    You can't demote or deactivate yourself, or the last active Super Admin.
    """
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def _get(self, pk):
        return PlatformAdmin.objects.select_related('invited_by').filter(pk=pk).first()

    def get(self, request, pk):
        admin = self._get(pk)
        if not admin:
            return Response({'error': 'Console user not found.'}, status=404)
        return Response(serialize_platform_user(admin))

    def patch(self, request, pk):
        admin = self._get(pk)
        if not admin:
            return Response({'error': 'Console user not found.'}, status=404)
        d = request.data
        if 'role' in d:
            if d['role'] not in dict(PlatformAdmin.ROLE_CHOICES):
                return Response({'role': 'Use super_admin or viewer.'}, status=400)
            if d['role'] != 'super_admin' and admin.role == 'super_admin':
                if admin.pk == request.user.pk:
                    return Response({'error': "You can't change your own role.", 'code': 'cannot_change_self'}, status=400)
                if _last_super_admin(admin):
                    return Response({'error': 'There must be at least one active Super Admin.',
                                     'code': 'last_super_admin'}, status=400)
            admin.role = d['role']
        if 'name' in d:
            name = str(d.get('name') or '').strip()
            if not name:
                return Response({'name': 'This field may not be blank.'}, status=400)
            admin.name = name[:150]
        if 'is_active' in d:
            active = d['is_active'] in (True, 'true', 'True', 1, '1')
            if not active:
                error = self._deactivation_error(request, admin)
                if error:
                    return error
            admin.is_active = active
        admin.save()
        return Response(serialize_platform_user(admin))

    def _deactivation_error(self, request, admin):
        if admin.pk == request.user.pk:
            return Response({'error': "You can't remove yourself.", 'code': 'cannot_change_self'}, status=400)
        if _last_super_admin(admin):
            return Response({'error': 'There must be at least one active Super Admin.', 'code': 'last_super_admin'}, status=400)
        return None

    def delete(self, request, pk):
        admin = self._get(pk)
        if not admin:
            return Response({'error': 'Console user not found.'}, status=404)
        error = self._deactivation_error(request, admin)
        if error:
            return error
        admin.is_active = False
        admin.save(update_fields=['is_active'])
        return Response({'message': f'{admin.email} has been removed and can no longer log in.',
                         'user': serialize_platform_user(admin)})


class PlatformUserResetPasswordView(APIView):
    """POST /api/platform/users/<id>/reset-password/  (Super Admin) → new temp_password, ends their sessions."""
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        admin = PlatformAdmin.objects.filter(pk=pk).first()
        if not admin:
            return Response({'error': 'Console user not found.'}, status=404)
        if admin.pk == request.user.pk:
            return Response({'error': 'Use change password for your own account.', 'code': 'cannot_change_self'}, status=400)
        temp_password = _temp_password()
        admin.set_password(temp_password)
        admin.must_change_password = True
        admin.save(update_fields=['password', 'must_change_password'])
        return Response({'id': admin.id, 'email': admin.email, 'temp_password': temp_password,
                         'must_change_password': True})


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
    data.update({'stripe_price_id': plan.stripe_price_id, 'stripe_product_id': plan.stripe_product_id or None,
                 'billable': bool(plan.stripe_price_id), 'is_active': plan.is_active,
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


class PlatformPlanStripeSyncView(APIView):
    """
    POST /api/platform/plans/<id>/stripe-sync/
    Creates the plan's Product + recurring Price in Stripe (using the server's STRIPE_SECRET_KEY, so it
    lands in the same test/live mode the backend uses) and saves stripe_price_id. If the plan's
    price / currency / interval changed since the last sync, a new Stripe Price is created and the old
    one archived (Stripe prices can't be edited). Existing subscriptions keep their old price.
    """
    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        stripe = b.stripe_client()
        if stripe is None:
            return Response({'error': 'Billing is not configured on the server (STRIPE_SECRET_KEY).',
                             'code': 'billing_not_configured'}, status=503)
        plan = Plan.objects.annotate(clinic_count=Count('clinics')).filter(pk=pk).first()
        if not plan:
            return Response({'error': 'Plan not found.'}, status=404)
        if plan.price <= 0:
            return Response({'price': 'Set a price above 0 first (PATCH /api/platform/plans/<id>/).'}, status=400)
        amount = int((plan.price * 100).to_integral_value())
        created_price = False
        try:
            if plan.stripe_product_id:
                stripe.Product.modify(plan.stripe_product_id, name=plan.name, active=True)
            else:
                product = stripe.Product.create(name=plan.name, metadata={'aura_plan_id': str(plan.id)},
                                                idempotency_key=f'aura-plan-{plan.id}-product')
                plan.stripe_product_id = product['id']
            current = None
            if plan.stripe_price_id:
                try:
                    current = stripe.Price.retrieve(plan.stripe_price_id)
                except stripe.error.InvalidRequestError:
                    current = None
            matches = current is not None and b._get(current, 'active', True) \
                and b._get(current, 'unit_amount') == amount \
                and str(b._get(current, 'currency', '')).lower() == plan.currency.lower() \
                and b._get(b._get(current, 'recurring', {}) or {}, 'interval') == plan.interval \
                and b._get(current, 'product') == plan.stripe_product_id
            if not matches:
                price = stripe.Price.create(product=plan.stripe_product_id, unit_amount=amount,
                                            currency=plan.currency.lower(), recurring={'interval': plan.interval},
                                            metadata={'aura_plan_id': str(plan.id)})
                if current is not None and b._get(current, 'active', False):
                    stripe.Price.modify(b._get(current, 'id'), active=False)
                plan.stripe_price_id = price['id']
                created_price = True
        except stripe.error.StripeError as e:
            return Response({'error': f'Stripe error: {getattr(e, "user_message", None) or str(e)}', 'code': 'stripe_error'}, status=502)
        plan.save()
        data = _plan_admin(plan)
        data['created_new_price'] = created_price
        return Response(data)
