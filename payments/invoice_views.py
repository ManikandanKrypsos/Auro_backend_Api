"""
Invoices and payment records (admin / reception).

GET    /api/invoices/                         list (filters below)
POST   /api/invoices/                         standalone invoice (no appointment)
GET    /api/invoices/<id>/                    detail with lines + payments
PATCH  /api/invoices/<id>/                    due_date, notes, lines (replaces all lines)
POST   /api/invoices/<id>/void/               only when nothing has been paid
GET    /api/invoices/for-appointment/<id>/    the appointment's invoice (created if missing)
GET    /api/invoices/settings/  PATCH          default_tax_rate, invoice_due_days (PATCH: admin)

POST   /api/payments/                          record a payment {invoice_id, amount, method, …}
GET    /api/payments/records/                  payment records (filters below)
GET    /api/payments/records/<id>/             one payment
"""
import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin, IsAdminOrReception
from utils.api_errors import error, validation_error
from utils.pagination import paginate
from . import invoicing as inv
from .models import Invoice, InvoiceLine, Payment


def _f(v):
    return round(float(v or 0), 2)


def _name(u):
    return (u.username or u.email.split('@')[0]) if u else None


def serialize_line(l):
    return {
        'id': l.id, 'description': l.description,
        'treatment_id': l.treatment_id, 'product_id': l.product_id,
        'quantity': _f(l.quantity), 'unit_price': _f(l.unit_price), 'tax_rate': _f(l.tax_rate),
        'line_total': _f(l.line_total), 'tax_amount': _f(l.tax_amount),
        'from_appointment': l.from_appointment,
    }


def serialize_payment(p, with_invoice=True):
    data = {
        'id': p.id, 'invoice_id': p.invoice_id, 'kind': p.kind,
        'amount': _f(p.amount), 'signed_amount': _f(p.amount if p.kind == 'payment' else -p.amount),
        'method': p.method, 'method_label': dict(Payment.METHOD_CHOICES).get(p.method, p.method),
        'paid_at': p.paid_at, 'date': timezone.localtime(p.paid_at).date().isoformat(),
        'reference': p.reference, 'note': p.note,
        'receipt_number': p.receipt_number,
        'receipt_url': f'/api/payments/records/{p.id}/receipt/',
        'reconciled': p.reconciled, 'reconciled_at': p.reconciled_at,
        'reconciled_by': {'id': p.reconciled_by_id, 'name': _name(p.reconciled_by)} if p.reconciled_by_id else None,
        'reconciliation_ref': p.reconciliation_ref,
        'created_by': {'id': p.created_by_id, 'name': _name(p.created_by)} if p.created_by_id else None,
        'created_at': p.created_at,
    }
    if p.kind == 'payment':
        data['refunded_amount'] = _f(p.amount - inv.refundable(p))
        data['refundable_amount'] = _f(inv.refundable(p))
    else:
        data['refund_of_id'] = p.refund_of_id
        data['reason'] = p.reason
        data['adjusts_invoice'] = p.adjusts_invoice
    if with_invoice:
        i = p.invoice
        data['invoice'] = {'id': i.id, 'invoice_number': i.invoice_number, 'status': i.status,
                           'patient_name': i.patient.name if i.patient_id and i.patient else None,
                           'balance_due': _f(i.balance_due)}
    return data


# ── Ageing ────────────────────────────────────────────────────────────────────
# Buckets by days past the due date, for invoices that still have something to pay.
AGEING_BUCKETS = (
    ('current', 'Not yet due',      None, 0),     # due today or later
    ('1_30',    '1–30 days overdue',  1, 30),
    ('31_60',   '31–60 days overdue', 31, 60),
    ('61_90',   '61–90 days overdue', 61, 90),
    ('90_plus', 'Over 90 days overdue', 91, None),
)
OWING = ('open', 'partially_paid')


def ageing_bucket(days_overdue):
    for key, _, low, high in AGEING_BUCKETS:
        if (low is None or days_overdue >= low) and (high is None or days_overdue <= high):
            return key
    return 'current'


def bucket_filter(qs, key, today):
    """Invoices still owing whose due date puts them in the bucket."""
    spec = {k: (lo, hi) for k, _, lo, hi in AGEING_BUCKETS}[key]
    qs = qs.filter(status__in=OWING, balance_due__gt=0)
    lo, hi = spec
    if key == 'current':
        return qs.filter(due_date__gte=today)
    qs = qs.filter(due_date__lte=today - datetime.timedelta(days=lo))
    if hi is not None:
        qs = qs.filter(due_date__gte=today - datetime.timedelta(days=hi))
    return qs


def serialize_invoice(i, detail=False):
    today = timezone.localdate()
    owed = i.balance_due > 0 and i.status in OWING
    appt = i.appointment if i.appointment_id else None
    data = {
        'id': i.id, 'invoice_number': i.invoice_number, 'status': i.status,
        'patient': {'id': i.patient.patient_id, 'db_id': i.patient.id, 'name': i.patient.name,
                    'phone': i.patient.phone} if i.patient_id and i.patient else None,
        'appointment_id': i.appointment_id,
        'appointment': {
            'date_time': appt.date_time,
            'treatment': appt.treatment.name if appt.treatment_id and appt.treatment else None,
            'staff_id': appt.staff_id, 'staff_name': _name(appt.staff) if appt.staff_id else None,
            'status': appt.status,
        } if appt else None,
        'issue_date': i.issue_date, 'due_date': i.due_date,
        'days_overdue': (today - i.due_date).days if owed and i.due_date < today else 0,
        'ageing_bucket': ageing_bucket((today - i.due_date).days) if owed else None,
        'currency': 'eur',
        'subtotal': _f(i.subtotal), 'tax_amount': _f(i.tax_amount), 'total': _f(i.total),
        'amount_paid': _f(i.amount_paid), 'credited': _f(i.credited), 'balance_due': _f(i.balance_due),
        'notes': i.notes, 'created_at': i.created_at, 'updated_at': i.updated_at,
    }
    if detail:
        data['lines'] = [serialize_line(l) for l in i.lines.all().select_related()]
        data['tax_breakdown'] = _tax_breakdown(data['lines'])
        data['payments'] = [serialize_payment(p, with_invoice=False)
                            for p in i.payments.select_related('created_by').order_by('paid_at', 'id')]
    return data


def _tax_breakdown(lines):
    rates = {}
    for l in lines:
        r = rates.setdefault(l['tax_rate'], {'tax_rate': l['tax_rate'], 'total': 0.0, 'tax_amount': 0.0})
        r['total'] = round(r['total'] + l['line_total'], 2)
        r['tax_amount'] = round(r['tax_amount'] + l['tax_amount'], 2)
    for r in rates.values():
        r['net'] = round(r['total'] - r['tax_amount'], 2)
    return sorted(rates.values(), key=lambda r: r['tax_rate'])


def _invoice_qs():
    return Invoice.objects.select_related('patient', 'appointment', 'appointment__treatment', 'appointment__staff')


def _get_invoice(pk):
    return _invoice_qs().filter(pk=pk).first()


def _dec(value, field, errors, minimum=None, maximum=None):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        errors[field] = 'Must be a number.'
        return None
    if not d.is_finite() or (minimum is not None and d < minimum) or (maximum is not None and d > maximum):
        errors[field] = f'Must be between {minimum} and {maximum}.' if maximum is not None else f'Must be {minimum} or more.'
        return None
    return d


def _parse_lines(raw, clinic_id, errors):
    """Validates the lines payload → unsaved InvoiceLine objects (no invoice yet)."""
    from inventory.models import InventoryItem
    from treatments.models import Treatment
    if not isinstance(raw, list) or not raw:
        errors['lines'] = 'Send at least one line.'
        return []
    if len(raw) > 50:
        errors['lines'] = 'At most 50 lines.'
        return []
    default_rate, _ = inv.clinic_settings(clinic_id)
    out = []
    for n, item in enumerate(raw):
        key = f'lines[{n}]'
        if not isinstance(item, dict):
            errors[key] = 'Each line must be an object.'
            continue
        e = {}
        treatment = product = None
        if item.get('treatment_id') not in (None, ''):
            treatment = Treatment.objects.filter(pk=item['treatment_id']).first() if str(item['treatment_id']).isdigit() else None
            if not treatment:
                e['treatment_id'] = 'Treatment not found.'
        if item.get('product_id') not in (None, ''):
            product = InventoryItem.objects.filter(pk=item['product_id']).first() if str(item['product_id']).isdigit() else None
            if not product:
                e['product_id'] = 'Product not found.'
        qty = _dec(item.get('quantity', 1), 'quantity', e, Decimal('0.01'), Decimal('9999'))
        price = item.get('unit_price')
        if price in (None, ''):
            price = treatment.price if treatment and treatment.price is not None else None
        if price in (None, ''):
            e['unit_price'] = 'This field is required.'
        else:
            price = _dec(price, 'unit_price', e, Decimal('0'), Decimal('1000000'))
        rate = item.get('tax_rate')
        rate = default_rate if rate in (None, '') else _dec(rate, 'tax_rate', e, Decimal('0'), Decimal('100'))
        desc = str(item.get('description') or '').strip() or (treatment.name if treatment else product.name if product else '')
        if not desc:
            e['description'] = 'This field is required.'
        if e:
            for k, v in e.items():
                errors[f'{key}.{k}'] = v
            continue
        out.append(inv.line_amounts(InvoiceLine(
            position=n, description=desc[:255], treatment=treatment, product=product,
            quantity=qty, unit_price=inv.money(price), tax_rate=rate,
        )))
    return out


def _date(value, field, errors):
    d = parse_date(str(value)) if value not in (None, '') else None
    if value not in (None, '') and not d:
        errors[field] = 'Use YYYY-MM-DD.'
    return d


class InvoiceListView(APIView):
    """
    GET /api/invoices/?status=open,partially_paid&patient_id=Aura41&appointment_id=&staff_id=
        &date_from=&date_to= (issue date)&overdue=true&search=&page=&page_size=
    POST /api/invoices/  {patient_id, lines: [...], issue_date?, due_date?, notes?}
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        p = request.query_params
        qs = _invoice_qs()
        errors = {}
        if p.get('status'):
            statuses = [s.strip() for s in p['status'].split(',') if s.strip()]
            bad = [s for s in statuses if s not in dict(Invoice.STATUS_CHOICES)]
            if bad:
                errors['status'] = f'Unknown status: {", ".join(bad)}.'
            qs = qs.filter(status__in=statuses)
        if p.get('patient_id'):
            pid = p['patient_id'].strip()
            qs = qs.filter(patient_id=int(pid)) if pid.isdigit() else qs.filter(patient__patient_id__iexact=pid)
        for field, lookup in (('appointment_id', 'appointment_id'), ('staff_id', 'appointment__staff_id')):
            if p.get(field):
                if not p[field].isdigit():
                    errors[field] = 'Must be an id.'
                else:
                    qs = qs.filter(**{lookup: int(p[field])})
        date_from, date_to = _date(p.get('date_from'), 'date_from', errors), _date(p.get('date_to'), 'date_to', errors)
        if date_from:
            qs = qs.filter(issue_date__gte=date_from)
        if date_to:
            qs = qs.filter(issue_date__lte=date_to)
        if p.get('overdue', '').lower() == 'true':
            qs = qs.filter(status__in=['open', 'partially_paid'], balance_due__gt=0, due_date__lt=timezone.localdate())
        if p.get('ageing'):
            keys = [k.strip() for k in p['ageing'].split(',') if k.strip()]
            valid = [k for k, *_ in AGEING_BUCKETS]
            if any(k not in valid for k in keys):
                errors['ageing'] = f'Use {", ".join(valid)} (comma-separate for several).'
            else:
                today = timezone.localdate()
                ids = set()
                for k in keys:
                    ids.update(bucket_filter(Invoice.objects.all(), k, today).values_list('id', flat=True))
                qs = qs.filter(id__in=ids)
        if p.get('search'):
            s = p['search'].strip()
            qs = qs.filter(Q(invoice_number__icontains=s) | Q(patient__name__icontains=s) | Q(patient__phone__icontains=s))
        if errors:
            return validation_error(errors)
        return paginate(request, qs.order_by('-issue_date', '-id'), lambda rows: [serialize_invoice(i) for i in rows])

    def post(self, request):
        from patients.models import Patient
        d = request.data
        errors = {}
        raw = str(d.get('patient_id', '') or '').strip()
        patient = None
        if not raw:
            errors['patient_id'] = 'This field is required.'
        else:
            patient = (Patient.objects.filter(pk=int(raw)).first() if raw.isdigit()
                       else Patient.objects.filter(patient_id__iexact=raw).first())
            if not patient:
                errors['patient_id'] = f"Patient '{raw}' not found."
        clinic_id = request.user.clinic_id
        lines = _parse_lines(d.get('lines'), clinic_id, errors)
        today = timezone.localdate()
        issue = _date(d.get('issue_date'), 'issue_date', errors) or today
        _, due_days = inv.clinic_settings(clinic_id)
        due = _date(d.get('due_date'), 'due_date', errors) or issue + datetime.timedelta(days=due_days)
        if due < issue:
            errors['due_date'] = 'Must be on or after the issue date.'
        if errors:
            return validation_error(errors)
        with transaction.atomic():
            invoice = Invoice.objects.create(
                clinic_id=clinic_id, patient=patient, issue_date=issue, due_date=due,
                invoice_number=inv.next_invoice_number(clinic_id, issue.year),
                notes=str(d.get('notes') or '')[:5000], created_by=request.user,
            )
            for l in lines:
                l.invoice = invoice
            InvoiceLine.objects.bulk_create(lines)
            inv.recalc(invoice)
        return Response(serialize_invoice(_get_invoice(invoice.pk), detail=True), status=201)


class InvoiceDetailNewView(APIView):
    """GET / PATCH /api/invoices/<id>/   PATCH: {due_date?, notes?, lines?} (lines replace all lines)"""
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        i = _get_invoice(pk)
        if not i:
            return error(404, 'invoice_not_found', 'Invoice not found.')
        return Response(serialize_invoice(i, detail=True))

    def patch(self, request, pk):
        i = _get_invoice(pk)
        if not i:
            return error(404, 'invoice_not_found', 'Invoice not found.')
        if i.status == 'void':
            return error(409, 'invoice_void', 'This invoice is void and can no longer be changed.')
        d, errors = request.data, {}
        lines = None
        if 'lines' in d:
            lines = _parse_lines(d.get('lines'), i.clinic_id, errors)
        due = _date(d.get('due_date'), 'due_date', errors) if 'due_date' in d else None
        if due and due < i.issue_date:
            errors['due_date'] = 'Must be on or after the issue date.'
        if errors:
            return validation_error(errors)
        if lines is not None:
            new_total = sum((l.line_total for l in lines), Decimal(0))
            if new_total - i.credited < i.amount_paid:
                return error(409, 'total_below_paid',
                             f'The new total ({new_total}) is less than what has already been paid ({i.amount_paid}). '
                             f'Refund the difference first.')
        with transaction.atomic():
            if lines is not None:
                auto = InvoiceLine.objects.filter(invoice=i, from_appointment=True).first()
                InvoiceLine.objects.filter(invoice=i).delete()
                for n, l in enumerate(lines):
                    l.invoice = i
                    # keep the appointment link on the line that has the appointment's treatment
                    if auto and n == 0 and l.treatment_id == auto.treatment_id:
                        l.from_appointment = True
                InvoiceLine.objects.bulk_create(lines)
            if due:
                i.due_date = due
            if 'notes' in d:
                i.notes = str(d.get('notes') or '')[:5000]
            inv.recalc(i)
        return Response(serialize_invoice(_get_invoice(i.pk), detail=True))


class InvoiceVoidView(APIView):
    """POST /api/invoices/<id>/void/  {reason?} — only when nothing has been paid (refund first otherwise)."""
    permission_classes = [IsAdminOrReception]

    def post(self, request, pk):
        i = _get_invoice(pk)
        if not i:
            return error(404, 'invoice_not_found', 'Invoice not found.')
        if i.amount_paid > 0:
            return error(409, 'invoice_has_payments', 'This invoice has payments. Refund them before voiding.')
        i.status, i.voided_automatically = 'void', False
        reason = str(request.data.get('reason') or '').strip()
        if reason:
            i.notes = (i.notes + '\n' if i.notes else '') + f'Voided: {reason}'[:500]
        inv.recalc(i)
        return Response(serialize_invoice(_get_invoice(i.pk), detail=True))


class AppointmentInvoiceView(APIView):
    """GET /api/invoices/for-appointment/<appointment_id>/ — creates the invoice if it doesn't exist yet."""
    permission_classes = [IsAdminOrReception]

    def get(self, request, appointment_id):
        from appointments.models import Appointment
        appt = Appointment.objects.select_related('treatment', 'price_plan').filter(pk=appointment_id).first()
        if not appt:
            return error(404, 'appointment_not_found', 'Appointment not found.')
        i = inv.invoice_for_appointment(appt, request.user)
        return Response(serialize_invoice(_get_invoice(i.pk), detail=True))


class InvoiceSettingsView(APIView):
    """
    GET (admin/reception) / PATCH (admin) /api/invoices/settings/
    {default_tax_rate, invoice_due_days, legal_name, tax_id, billing_address, billing_phone, billing_email}
    The billing details are printed on receipts.
    """

    def get_permissions(self):
        return [IsAdmin()] if self.request.method == 'PATCH' else [IsAdminOrReception()]

    TEXT_FIELDS = {'legal_name': 200, 'tax_id': 40, 'billing_address': 1000, 'billing_phone': 40, 'billing_email': 254}

    def _payload(self, clinic):
        data = {'default_tax_rate': _f(clinic.default_tax_rate), 'invoice_due_days': clinic.invoice_due_days,
                'prices_include_tax': True, 'currency': 'eur', 'clinic_name': clinic.name}
        data.update({f: getattr(clinic, f) for f in self.TEXT_FIELDS})
        return data

    def get(self, request):
        return Response(self._payload(request.user.clinic))

    def patch(self, request):
        clinic = request.user.clinic
        errors = {}
        if 'default_tax_rate' in request.data:
            rate = _dec(request.data['default_tax_rate'], 'default_tax_rate', errors, Decimal('0'), Decimal('100'))
            if rate is not None:
                clinic.default_tax_rate = rate
        if 'invoice_due_days' in request.data:
            raw = str(request.data['invoice_due_days'])
            if not raw.isdigit() or int(raw) > 365:
                errors['invoice_due_days'] = 'Whole number of days between 0 and 365.'
            else:
                clinic.invoice_due_days = int(raw)
        for f, limit in self.TEXT_FIELDS.items():
            if f in request.data:
                value = str(request.data.get(f) or '').strip()
                if len(value) > limit:
                    errors[f] = f'At most {limit} characters.'
                elif f == 'billing_email' and value:
                    from django.core.exceptions import ValidationError as DjangoValidationError
                    from django.core.validators import validate_email
                    try:
                        validate_email(value)
                    except DjangoValidationError:
                        errors[f] = 'Enter a valid email address.'
                setattr(clinic, f, value)
        if errors:
            return validation_error(errors)
        clinic.save(update_fields=['default_tax_rate', 'invoice_due_days', 'updated_at', *self.TEXT_FIELDS])
        return Response(self._payload(clinic))


# ── Payment records ───────────────────────────────────────────────────────────

def record_payment(request):
    """POST /api/payments/  {invoice_id, amount, method, paid_at?, reference?, note?}"""
    d, errors = request.data, {}
    raw = str(d.get('invoice_id', '') or '').strip()
    invoice = None
    if not raw:
        errors['invoice_id'] = 'This field is required.'
    elif not raw.isdigit():
        errors['invoice_id'] = 'Must be an invoice id.'
    amount = _dec(d.get('amount'), 'amount', errors, Decimal('0.01')) if d.get('amount') not in (None, '') else None
    if amount is None and 'amount' not in errors:
        errors['amount'] = 'This field is required.'
    method = str(d.get('method', '') or '').strip()
    if method not in inv.METHODS:
        errors['method'] = f'Use one of: {", ".join(inv.METHODS)}.'
    paid_at = None
    if d.get('paid_at'):
        paid_at = parse_datetime(str(d['paid_at']))
        if paid_at is None:
            day = parse_date(str(d['paid_at']))
            paid_at = timezone.make_aware(datetime.datetime.combine(day, datetime.time(12))) if day else None
        if paid_at is None:
            errors['paid_at'] = 'Use YYYY-MM-DD or an ISO date-time.'
        elif timezone.is_naive(paid_at):
            paid_at = timezone.make_aware(paid_at)
        if paid_at and paid_at > timezone.now() + datetime.timedelta(minutes=5):
            errors['paid_at'] = "Can't be in the future."
    if errors:
        return validation_error(errors)
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().filter(pk=int(raw)).first()
        if not invoice:
            return error(404, 'invoice_not_found', 'Invoice not found.')
        try:
            payment = inv.add_payment(invoice, amount, method, user=request.user, paid_at=paid_at,
                                      reference=d.get('reference', ''), note=d.get('note', ''))
        except inv.PaymentError as e:
            status = 400 if e.field else 409
            return error(status, e.code, e.message, {e.field: e.message} if e.field else None)
    data = serialize_payment(Payment.objects.select_related('invoice', 'invoice__patient', 'created_by').get(pk=payment.pk))
    data['invoice'] = serialize_invoice(_get_invoice(invoice.pk))
    return Response(data, status=201)


class PaymentRecordListView(APIView):
    """
    GET /api/payments/records/?invoice_id=&patient_id=&method=cash,card&kind=payment|refund
        &date_from=&date_to= (by paid date)&staff_id=&reconciled=true|false&reconciliation_ref=&page=&page_size=
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        p, errors = request.query_params, {}
        qs = Payment.objects.select_related('invoice', 'invoice__patient', 'created_by', 'reconciled_by')
        raw = str(p.get('reconciled', '') or '').lower()
        if raw in ('true', 'false'):
            qs = qs.filter(reconciled=(raw == 'true'))
        elif raw:
            errors['reconciled'] = 'Use true or false.'
        if p.get('reconciliation_ref'):
            qs = qs.filter(reconciliation_ref__iexact=p['reconciliation_ref'].strip())
        if p.get('invoice_id'):
            qs = qs.filter(invoice_id=p['invoice_id']) if p['invoice_id'].isdigit() else qs.none()
        if p.get('patient_id'):
            pid = p['patient_id'].strip()
            qs = qs.filter(invoice__patient_id=int(pid)) if pid.isdigit() else qs.filter(invoice__patient__patient_id__iexact=pid)
        if p.get('staff_id'):
            qs = qs.filter(invoice__appointment__staff_id=p['staff_id']) if p['staff_id'].isdigit() else qs.none()
        if p.get('method'):
            methods = [m.strip() for m in p['method'].split(',') if m.strip()]
            if any(m not in inv.METHODS for m in methods):
                errors['method'] = f'Use one of: {", ".join(inv.METHODS)}.'
            qs = qs.filter(method__in=methods)
        if p.get('kind'):
            if p['kind'] not in ('payment', 'refund'):
                errors['kind'] = 'Use payment or refund.'
            qs = qs.filter(kind=p['kind'])
        date_from, date_to = _date(p.get('date_from'), 'date_from', errors), _date(p.get('date_to'), 'date_to', errors)
        from .metrics import day_start
        if date_from:
            qs = qs.filter(paid_at__gte=day_start(date_from))
        if date_to:
            qs = qs.filter(paid_at__lt=day_start(date_to + datetime.timedelta(days=1)))
        if errors:
            return validation_error(errors)
        return paginate(request, qs.order_by('-paid_at', '-id'), lambda rows: [serialize_payment(x) for x in rows])


class PaymentRecordDetailView(APIView):
    """GET /api/payments/records/<id>/"""
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        p = Payment.objects.select_related('invoice', 'invoice__patient', 'created_by').filter(pk=pk).first()
        if not p:
            return error(404, 'payment_not_found', 'Payment not found.')
        data = serialize_payment(p)
        data['invoice'] = serialize_invoice(_get_invoice(p.invoice_id))
        return Response(data)


class PaymentRefundView(APIView):
    """
    POST /api/payments/records/<id>/refund/
    {"amount": 20, "reason": "Treatment shortened", "adjust_invoice": true, "record_only": false}
    amount: optional (default = everything still refundable on this payment).
    adjust_invoice (default true): the refund also lowers what is owed. false = the amount goes back
    onto the balance (e.g. refunded to the wrong card, to be collected again).
    Online payments are refunded through Stripe; record_only: true just records a refund already
    made in Stripe.
    """
    permission_classes = [IsAdminOrReception]

    def post(self, request, pk):
        d, errors = request.data, {}
        reason = str(d.get('reason', '') or '').strip()
        if not reason:
            errors['reason'] = 'This field is required.'
        amount = None
        if d.get('amount') not in (None, ''):
            amount = _dec(d.get('amount'), 'amount', errors, Decimal('0.01'))
        flags = {}
        for f, default in (('adjust_invoice', True), ('record_only', False)):
            v = d.get(f, default)
            if v not in (True, False, 'true', 'false'):
                errors[f] = 'Use true or false.'
            flags[f] = v in (True, 'true')
        if errors:
            return validation_error(errors)
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('invoice').filter(pk=pk).first()
            if not payment:
                return error(404, 'payment_not_found', 'Payment not found.')
            Invoice.objects.select_for_update().filter(pk=payment.invoice_id).first()
            try:
                refund = inv.refund_payment(payment, amount, reason=reason, user=request.user,
                                            adjust_invoice=flags['adjust_invoice'], record_only=flags['record_only'])
            except inv.PaymentError as e:
                status = 400 if e.field else (502 if e.code == 'stripe_error' else 409)
                return error(status, e.code, e.message, {e.field: e.message} if e.field else None)
        data = serialize_payment(Payment.objects.select_related('invoice', 'invoice__patient', 'created_by').get(pk=refund.pk))
        data['invoice'] = serialize_invoice(_get_invoice(payment.invoice_id))
        data['original_payment'] = serialize_payment(Payment.objects.select_related('invoice', 'created_by').get(pk=payment.pk),
                                                     with_invoice=False)
        return Response(data, status=201)


class PaymentReceiptView(APIView):
    """
    GET /api/payments/records/<id>/receipt/              JSON (to render in the app)
    GET /api/payments/records/<id>/receipt/?output=pdf   PDF download
    One receipt per payment (each instalment) and per refund.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        from .receipts import receipt_data, receipt_pdf
        p = (Payment.objects.select_related('invoice', 'invoice__patient', 'invoice__appointment',
                                            'invoice__appointment__treatment', 'created_by', 'refund_of')
             .filter(pk=pk).first())
        if not p:
            return error(404, 'payment_not_found', 'Payment not found.')
        data = receipt_data(p)
        if request.query_params.get('output') == 'pdf':
            from django.http import HttpResponse
            resp = HttpResponse(receipt_pdf(data), content_type='application/pdf')
            resp['Content-Disposition'] = f'attachment; filename="{data["receipt_number"] or "receipt"}.pdf"'
            return resp
        return Response(data)


class AgeingReportView(APIView):
    """
    GET /api/invoices/ageing/?staff_id=8&patient_id=Aura41&top=20
    What is still owed, grouped by how far past the due date it is, for the whole clinic
    (or one therapist / one patient). Only open and partially paid invoices count.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        from django.db.models import Count, Max, Min, Sum
        p, errors = request.query_params, {}
        today = timezone.localdate()
        base = Invoice.objects.filter(status__in=OWING, balance_due__gt=0)
        if p.get('staff_id'):
            if not p['staff_id'].isdigit():
                errors['staff_id'] = 'Must be an id.'
            else:
                base = base.filter(appointment__staff_id=int(p['staff_id']))
        if p.get('patient_id'):
            pid = p['patient_id'].strip()
            base = base.filter(patient_id=int(pid)) if pid.isdigit() else base.filter(patient__patient_id__iexact=pid)
        top = 20
        if p.get('top'):
            if not p['top'].isdigit() or not 1 <= int(p['top']) <= 100:
                errors['top'] = 'Whole number between 1 and 100.'
            else:
                top = int(p['top'])
        if errors:
            return validation_error(errors)

        buckets = []
        for key, label, lo, hi in AGEING_BUCKETS:
            agg = bucket_filter(base, key, today).aggregate(n=Count('id'), t=Sum('balance_due'))
            buckets.append({'key': key, 'label': label, 'min_days': lo, 'max_days': hi,
                            'count': agg['n'], 'amount': _f(agg['t'])})
        total = round(sum(b['amount'] for b in buckets), 2)
        overdue = round(sum(b['amount'] for b in buckets if b['key'] != 'current'), 2)
        for b in buckets:
            b['pct'] = round(b['amount'] / total * 100, 1) if total else 0.0

        # who owes the most (overdue first, then everything owed)
        rows = (base.exclude(patient_id=None).values('patient_id', 'patient__patient_id', 'patient__name', 'patient__phone')
                .annotate(amount=Sum('balance_due'), invoices=Count('id'), oldest_due=Min('due_date'))
                .order_by('-amount')[:top])
        overdue_by_patient = dict(base.filter(due_date__lt=today).values('patient_id')
                                  .annotate(t=Sum('balance_due')).values_list('patient_id', 't'))
        patients = [{
            'patient': {'id': r['patient__patient_id'], 'db_id': r['patient_id'], 'name': r['patient__name'],
                        'phone': r['patient__phone']},
            'amount': _f(r['amount']), 'overdue_amount': _f(overdue_by_patient.get(r['patient_id'])),
            'invoices': r['invoices'], 'oldest_due_date': r['oldest_due'],
            'max_days_overdue': max((today - r['oldest_due']).days, 0) if r['oldest_due'] else 0,
        } for r in rows]

        oldest = base.aggregate(d=Min('due_date'))['d']
        return Response({
            'as_of': today,
            'currency': 'eur',
            'total_outstanding': total,
            'total_overdue': overdue,
            'invoice_count': sum(b['count'] for b in buckets),
            'oldest_due_date': oldest,
            'buckets': buckets,
            'top_patients': patients,
        })


# ── Reconciliation (back office) ──────────────────────────────────────────────

class ReconcileView(APIView):
    """
    POST /api/payments/records/reconcile/   (admin)
    {"payment_ids": [905, 906], "reconciled": true, "reference": "BBVA statement 2026-11"}
    Marks payments / refunds as matched (reconciled: false undoes it). Max 500 ids per call.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        d, errors = request.data, {}
        ids = d.get('payment_ids')
        if not isinstance(ids, list) or not ids:
            errors['payment_ids'] = 'Send a list of payment ids.'
        elif len(ids) > 500:
            errors['payment_ids'] = 'At most 500 ids per call.'
        elif any(isinstance(x, bool) or not str(x).isdigit() for x in ids):
            errors['payment_ids'] = 'Ids must be whole numbers.'
        value = d.get('reconciled', True)
        if value not in (True, False, 'true', 'false'):
            errors['reconciled'] = 'Use true or false.'
        reference = str(d.get('reference', '') or '').strip()
        if len(reference) > 120:
            errors['reference'] = 'At most 120 characters.'
        if errors:
            return validation_error(errors)
        value = value in (True, 'true')
        wanted = {int(x) for x in ids}
        qs = Payment.objects.filter(pk__in=wanted)           # other clinics' ids are simply not found
        found = set(qs.values_list('pk', flat=True))
        unchanged = set(qs.filter(reconciled=value).values_list('pk', flat=True))
        to_change = qs.exclude(pk__in=unchanged)
        if value:
            updated = to_change.update(reconciled=True, reconciled_at=timezone.now(), reconciled_by=request.user,
                                       reconciliation_ref=reference[:120])
            if reference and unchanged:   # already reconciled: a new reference replaces the old one
                Payment.objects.filter(pk__in=unchanged).update(reconciliation_ref=reference[:120])
        else:
            updated = to_change.update(reconciled=False, reconciled_at=None, reconciled_by=None, reconciliation_ref='')
        rows = Payment.objects.select_related('invoice', 'invoice__patient', 'created_by', 'reconciled_by') \
            .filter(pk__in=found).order_by('paid_at', 'id')
        return Response({
            'reconciled': value,
            'updated': updated,
            'already': len(unchanged),
            'not_found': sorted(wanted - found),
            'payments': [serialize_payment(x) for x in rows],
        })


class ReconciliationSummaryView(APIView):
    """
    GET /api/payments/reconciliation/?date_from=2026-11-01&date_to=2026-11-30&method=card
    Per method: what came in (payments − refunds) and how much of it is reconciled / still to match.
    Default period: this month.
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request):
        from django.db.models import Count, Sum
        from .metrics import payments_between, signed_amount, month_bounds
        p, errors = request.query_params, {}
        first, last = month_bounds(timezone.localdate())
        date_from = _date(p.get('date_from'), 'date_from', errors) or first
        date_to = _date(p.get('date_to'), 'date_to', errors) or last
        if date_from > date_to:
            errors['date_to'] = 'Must be on or after date_from.'
        methods = list(inv.METHODS)
        if p.get('method'):
            methods = [m.strip() for m in p['method'].split(',') if m.strip()]
            if any(m not in inv.METHODS for m in methods):
                errors['method'] = f'Use one of: {", ".join(inv.METHODS)}.'
        if errors:
            return validation_error(errors)
        qs = payments_between(date_from, date_to).filter(method__in=methods)
        rows = {(r['method'], r['reconciled']): r for r in
                qs.values('method', 'reconciled').annotate(n=Count('id'), t=Sum(signed_amount()))}
        out, tot = [], {'count': 0, 'net': 0.0, 'reconciled_count': 0, 'reconciled_net': 0.0}
        for m in methods:
            done, todo = rows.get((m, True), {}), rows.get((m, False), {})
            item = {
                'method': m, 'method_label': dict(Payment.METHOD_CHOICES)[m],
                'count': (done.get('n') or 0) + (todo.get('n') or 0),
                'net': _f((done.get('t') or 0) + (todo.get('t') or 0)),
                'reconciled_count': done.get('n') or 0, 'reconciled_net': _f(done.get('t')),
                'unreconciled_count': todo.get('n') or 0, 'unreconciled_net': _f(todo.get('t')),
            }
            out.append(item)
            for k in tot:
                tot[k] = round(tot[k] + item[k], 2) if isinstance(tot[k], float) else tot[k] + item[k]
        tot['unreconciled_count'] = tot['count'] - tot['reconciled_count']
        tot['unreconciled_net'] = round(tot['net'] - tot['reconciled_net'], 2)
        return Response({'date_from': date_from, 'date_to': date_to, 'currency': 'eur',
                         'totals': tot, 'methods': out})
