"""
Patient documents — consents plus ID copies, referral letters, lab results and other files.
Same table as the consent records (patients.ConsentRecord), so the per-patient consent endpoints
keep working (they show only type "consent").

GET    /api/documents/              clinic-wide queue, pending signature first
         ?patient_id= ?type=consent,lab_result ?status=pending,signed,not_required ?appointment_id=
         ?date_from= ?date_to= (upload date) ?search= (title / file name / patient)
         opt-in pagination ?page= &page_size=
GET    /api/documents/counts/       {total, pending, signed, not_required, by_type}
GET    /api/documents/types/        type + status choices
POST   /api/documents/              multipart: patient_id, type, file (PDF / image, max 10 MB) or file_url,
                                    title?, notes?, appointment_id?, and for consents: status?,
                                    patient_signed?, therapist_signed?, signed_date?
GET    /api/documents/<id>/
PATCH  /api/documents/<id>/         any of the POST fields (a new file replaces the old one)
DELETE /api/documents/<id>/

Who: admin + reception — everything. Therapists — read only, and only for patients they can open
(treated or added by them).
"""
import time

from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsClinicStaff
from utils import storage
from utils.api_errors import error, validation_error
from .models import ConsentRecord, Patient

TYPES = dict(ConsentRecord.TYPE_CHOICES)
STATUSES = dict(ConsentRecord.STATUS_CHOICES)
WRITE_ROLES = ('admin', 'reception')
TRUE = ('true', '1', 'yes', 'on')


def _role(request):
    return getattr(request.user, 'role', '') or ''


def _name(u):
    return (u.username or u.email.split('@')[0]) if u else None


def _bool(v):
    return v if isinstance(v, bool) else str(v).strip().lower() in TRUE


def _visible(request):
    qs = ConsentRecord.objects.select_related('patient', 'uploaded_by')
    if _role(request) == 'therapist':
        u = request.user
        qs = qs.filter(Q(patient__appointments__staff=u) | Q(patient__created_by=u)).distinct()
    return qs


def serialize(d):
    p = d.patient
    return {
        'id': d.id,
        'type': d.type, 'type_label': TYPES.get(d.type, d.type),
        'title': d.title, 'notes': d.notes,
        'file_name': d.file_name, 'file_url': d.file_url or None,
        'status': d.status, 'status_label': STATUSES.get(d.status, d.status),
        'needs_signature': d.status == 'pending',
        'patient_signed': d.patient_signed, 'therapist_signed': d.therapist_signed,
        'signed_date': str(d.signed_date) if d.signed_date else None,
        'appointment_id': d.appointment_id,
        'patient_id': p.patient_id, 'patient_db_id': p.id, 'patient_name': p.name, 'patient_phone': p.phone,
        'uploaded_by': _name(d.uploaded_by),
        'created_at': d.created_at.isoformat(),
        'updated_at': d.updated_at.isoformat() if d.updated_at else None,
    }


def _patient(value):
    v = str(value or '').strip()
    if not v:
        return None
    p = Patient.objects.filter(patient_id__iexact=v).first()
    if p is None and v.isdigit():
        p = Patient.objects.filter(pk=int(v)).first()
    return p


def _apply(doc, request, errors, creating):
    """Validate + set fields from the request. Returns the uploaded file (saved later) or None."""
    from appointments.models import Appointment
    from utils.upload_security import checked_ext
    d = request.data
    if creating or 'type' in d:
        t = str(d.get('type') or '').strip()
        if t not in TYPES:
            errors['type'] = f'Use one of: {", ".join(TYPES)}.'
        else:
            doc.type = t
    for f, n in (('title', 150), ('file_name', 255)):
        if f in d:
            v = str(d.get(f) or '').strip()
            if len(v) > n:
                errors[f] = f'At most {n} characters.'
            setattr(doc, f, v[:n])
    if 'notes' in d:
        doc.notes = str(d.get('notes') or '')
    if 'appointment_id' in d:
        v = d.get('appointment_id')
        if v in (None, '', 'null'):
            doc.appointment = None
        else:
            a = Appointment.objects.filter(pk=int(v)).first() if str(v).isdigit() else None
            if a is None or a.patient_id != doc.patient_id:
                errors['appointment_id'] = 'Appointment not found for this patient.'
            else:
                doc.appointment = a
    upload = request.FILES.get('file')
    if upload is not None:
        try:
            checked_ext(upload, 'document', '.pdf')
        except ValidationError as e:
            detail = e.detail.get('file') if isinstance(e.detail, dict) else e.detail
            errors['file'] = str(detail[0] if isinstance(detail, list) else detail)
    elif 'file_url' in d:
        doc.file_url = str(d.get('file_url') or '').strip()

    # signing — consents only
    if doc.type == 'consent':
        if doc.status == 'not_required':
            doc.status = 'pending'
        for f in ('patient_signed', 'therapist_signed'):
            if f in d:
                setattr(doc, f, _bool(d.get(f)))
        if 'status' in d:
            if d['status'] not in ('pending', 'signed'):
                errors['status'] = 'For a consent use pending or signed.'
            else:
                doc.status = d['status']
        if 'signed_date' in d:
            v = d.get('signed_date')
            if v in (None, '', 'null'):
                doc.signed_date = None
            else:
                sd = parse_date(str(v))
                if not sd:
                    errors['signed_date'] = 'Use YYYY-MM-DD.'
                else:
                    doc.signed_date = sd
        if doc.status == 'signed' and not doc.signed_date:
            doc.signed_date = timezone.localdate()
        if doc.status == 'pending' and 'signed_date' not in d:
            doc.signed_date = None
    else:
        doc.status = 'not_required'
        doc.patient_signed = doc.therapist_signed = False
        doc.signed_date = None
        if creating and upload is None and not doc.file_url:
            errors['file'] = 'Attach a file (or file_url) — only consents can be created without one.'
    if not errors and not doc.title:
        doc.title = (upload.name if upload is not None else doc.file_name) or TYPES.get(doc.type, 'Document')
        doc.title = doc.title[:150]
    return upload


def _store(doc, upload, request):
    from utils.upload_security import checked_ext, random_token
    ext = checked_ext(upload, 'document', '.pdf')
    old = doc.file_url
    doc.file_url = storage.store(upload, 'documents', f'doc_{doc.patient_id}_{int(time.time())}_{random_token()}{ext}', request)
    doc.file_name = (upload.name or doc.file_name)[:255]
    return old


class DocumentListView(APIView):
    permission_classes = [IsClinicStaff]

    def get(self, request):
        from utils.pagination import paginate
        p, qs = request.query_params, _visible(request)
        errors = {}
        if p.get('patient_id'):
            patient = _patient(p['patient_id'])
            qs = qs.filter(patient=patient) if patient else qs.none()
        for f, field in (('type', 'type'), ('status', 'status')):
            if p.get(f):
                qs = qs.filter(**{f'{field}__in': [x.strip() for x in p[f].split(',') if x.strip()]})
        if p.get('appointment_id'):
            if not str(p['appointment_id']).isdigit():
                errors['appointment_id'] = 'Must be a whole number.'
            else:
                qs = qs.filter(appointment_id=int(p['appointment_id']))
        for f, op in (('date_from', 'gte'), ('date_to', 'lte')):
            if p.get(f):
                d = parse_date(p[f])
                if not d:
                    errors[f] = 'Use YYYY-MM-DD.'
                else:
                    qs = qs.filter(**{f'created_at__date__{op}': d})
        if p.get('search'):
            s = p['search'].strip()
            qs = qs.filter(Q(title__icontains=s) | Q(file_name__icontains=s) | Q(patient__name__icontains=s)
                           | Q(patient__patient_id__iexact=s))
        if errors:
            return validation_error(errors)
        qs = qs.annotate(_pending=Case(When(status='pending', then=Value(0)), default=Value(1),
                                       output_field=IntegerField())).order_by('_pending', '-created_at', '-id')
        return paginate(request, qs, lambda rows: [serialize(d) for d in rows])

    def post(self, request):
        if _role(request) not in WRITE_ROLES:
            return error(403, 'not_permitted', 'Only admin or reception can upload documents.')
        patient = _patient(request.data.get('patient_id'))
        if not patient:
            return validation_error({'patient_id': 'Patient not found.'})
        doc = ConsentRecord(patient=patient, uploaded_by=request.user, status='pending', title='')
        errors = {}
        upload = _apply(doc, request, errors, creating=True)
        if errors:
            return validation_error(errors)
        with transaction.atomic():
            if upload is not None:
                _store(doc, upload, request)
            doc.save()
        return Response(serialize(doc), status=201)


class DocumentDetailView(APIView):
    permission_classes = [IsClinicStaff]

    def _get(self, request, pk):
        return _visible(request).filter(pk=pk).first()

    def get(self, request, pk):
        d = self._get(request, pk)
        if not d:
            return error(404, 'document_not_found', 'Document not found.')
        return Response(serialize(d))

    def patch(self, request, pk):
        if _role(request) not in WRITE_ROLES:
            return error(403, 'not_permitted', 'Only admin or reception can change documents.')
        d = self._get(request, pk)
        if not d:
            return error(404, 'document_not_found', 'Document not found.')
        errors = {}
        upload = _apply(d, request, errors, creating=False)
        if errors:
            return validation_error(errors)
        old = _store(d, upload, request) if upload is not None else None
        d.save()
        if old and old != d.file_url:
            storage.delete(old)
        return Response(serialize(d))

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        if _role(request) not in WRITE_ROLES:
            return error(403, 'not_permitted', 'Only admin or reception can delete documents.')
        d = self._get(request, pk)
        if not d:
            return error(404, 'document_not_found', 'Document not found.')
        ref = d.file_url
        d.delete()
        storage.delete(ref)
        return Response({'message': 'Document deleted.'})


class DocumentCountsView(APIView):
    permission_classes = [IsClinicStaff]

    def get(self, request):
        from django.db.models import Count
        qs = _visible(request)
        if request.query_params.get('patient_id'):
            patient = _patient(request.query_params['patient_id'])
            qs = qs.filter(patient=patient) if patient else qs.none()
        by_status = dict(qs.order_by().values_list('status').annotate(n=Count('id', distinct=True)))
        by_type = dict(qs.order_by().values_list('type').annotate(n=Count('id', distinct=True)))
        return Response({'total': sum(by_status.values()),
                         'pending': by_status.get('pending', 0), 'signed': by_status.get('signed', 0),
                         'not_required': by_status.get('not_required', 0),
                         'by_type': {t: by_type.get(t, 0) for t in TYPES}})


class DocumentTypesView(APIView):
    permission_classes = [IsClinicStaff]

    def get(self, request):
        return Response({'types': [{'value': k, 'label': v, 'needs_signature': k == 'consent'} for k, v in TYPES.items()],
                         'statuses': [{'value': k, 'label': v} for k, v in STATUSES.items()]})
