# Add these views to patients/views.py (or a separate file and include in urls)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminOrReception
from django.utils import timezone
from django.db.models import Count, Q
import datetime


def _get_patient(pk, user=None):
    """Patient by DB id or Aura id — None if missing or not visible to this therapist."""
    from patients.models import Patient
    from patients.access import can_access_patient
    try:
        if str(pk).isdigit():
            patient = Patient.objects.get(id=int(pk))
        else:
            patient = Patient.objects.get(patient_id__iexact=pk)
    except Patient.DoesNotExist:
        return None
    if user is not None and not can_access_patient(user, patient):
        return None
    return patient


class PatientOverviewView(APIView):
    """
    GET /api/patients/<id>/overview/
    Returns: upcoming appointment, active packages, allergy warning, patient activity timeline.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from patients.models import Patient
        from appointments.models import Appointment
        from appointments.serializers import AppointmentSerializer

        patient = _get_patient(pk, request.user)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        now   = timezone.now()
        today = timezone.localdate()

        # Next upcoming appointment
        next_appt = Appointment.objects.filter(
            patient=patient,
            date_time__gte=now,
            status='upcoming'
        ).select_related('staff', 'treatment', 'price_plan').order_by('date_time').first()

        def fmt_appt(a):
            if not a:
                return None
            from django.utils import timezone as tz
            dt = tz.localtime(a.date_time) if tz.is_aware(a.date_time) else a.date_time
            plan = a.price_plan
            return {
                'id':             a.id,
                'date':           str(dt.date()),
                'time':           dt.strftime('%H:%M'),
                'treatment':      a.treatment.name if a.treatment else None,
                'therapist':      a.staff.username if a.staff else None,
                'duration':       a.duration,
                'status':         a.status,
                'session_number': a.session_number,
                'total_sessions': plan.sessions if plan else a.total_sessions,
            }

        # Active packages (one query: every appointment of the patient that has a price plan)
        by_plan = {}
        for a in (Appointment.objects.filter(patient=patient, price_plan__isnull=False)
                  .select_related('price_plan', 'treatment', 'staff').order_by('date_time')):
            by_plan.setdefault(a.price_plan_id, []).append(a)
        active_packages = []
        for plan_id, appts_in_plan in by_plan.items():
            first     = appts_in_plan[0]
            plan      = first.price_plan
            total_sessions = plan.sessions if plan else first.total_sessions
            completed = sum(1 for a in appts_in_plan if a.status == 'completed')

            # Only show if not all sessions completed
            if completed >= total_sessions:
                continue

            next_a = next((a for a in appts_in_plan if a.status == 'upcoming' and a.date_time >= now), None)
            active_packages.append({
                'plan_id':        plan_id,
                'package_name':   first.treatment.name if first.treatment else '',
                'therapist':      first.staff.username if first.staff else None,
                'sessions_used':  completed,
                'total_sessions': total_sessions,
                'next_date':      str(next_a.date_time.date()) if next_a else None,
            })

        # Patient activity timeline
        activity = []

        # Appointments
        for a in Appointment.objects.filter(
            patient=patient
        ).select_related('staff', 'treatment', 'price_plan').order_by('-date_time')[:20]:
            from django.utils import timezone as tz
            dt   = tz.localtime(a.date_time) if tz.is_aware(a.date_time) else a.date_time
            plan = a.price_plan
            activity.append({
                'type':     'treatment',
                'date':     str(dt.date()),
                'title':    f"{a.treatment.name if a.treatment else 'Treatment'} — Session {a.session_number} of {plan.sessions if plan else a.total_sessions}",
                'subtitle': f"{a.staff.username if a.staff else ''} · {a.duration} min · €{a.payment_amount or ''}",
                'status':   a.status,
            })

        # Session notes
        from patients.models import SessionNote
        for n in SessionNote.objects.filter(patient=patient).order_by('-created_at')[:10]:
            activity.append({
                'type':     'note',
                'date':     str(n.created_at.date()),
                'title':    'Session Note Added',
                'subtitle': n.skin_observation[:80] if n.skin_observation else '',
            })

        # Consent records
        from patients.models import ConsentRecord
        for c in ConsentRecord.objects.filter(patient=patient).order_by('-created_at')[:10]:
            is_consent = c.type == 'consent'
            activity.append({
                'type':     'consent' if is_consent else 'document',
                'date':     str(c.created_at.date()),
                'title':    'Consent Form Added' if is_consent else 'Document Added',
                'subtitle': f"{c.title or 'Consent'} · {c.status.capitalize() if c.status else ''}" if is_consent
                            else f"{c.title} · {c.get_type_display()}",
            })

        # Payments
        for a in Appointment.objects.filter(
            patient=patient,
            payment_status='paid',
            payment_amount__isnull=False
        ).select_related('price_plan', 'treatment').order_by('-date_time')[:5]:
            from django.utils import timezone as tz
            dt   = tz.localtime(a.date_time) if tz.is_aware(a.date_time) else a.date_time
            plan = a.price_plan
            activity.append({
                'type':     'payment',
                'date':     str(dt.date()),
                'title':    'Payment Received',
                'subtitle': f"€{a.payment_amount} · {a.treatment.name if a.treatment else ''} · {plan.sessions if plan else ''} Sessions",
            })

        activity.sort(key=lambda x: x['date'], reverse=True)

        return Response({
            'patient_id':           patient.patient_id,
            'name':                 patient.name,
            'category':             patient.category,
            'allergy_warning':      patient.allergies if hasattr(patient, 'allergies') else None,
            'upcoming_appointment': fmt_appt(next_appt),
            'active_packages':      active_packages,
            'patient_activity':     activity[:15],
        })


class PatientHistoryView(APIView):
    """
    GET /api/patients/<id>/history/
    Returns treatment timeline with stats: total, completed, cancelled, scheduled.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from appointments.models import Appointment
        patient = _get_patient(pk, request.user)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        appts = Appointment.objects.filter(
            patient=patient
        ).select_related('staff', 'treatment', 'room_fk', 'price_plan').order_by('-date_time')

        counts    = dict(appts.order_by().values_list('status').annotate(n=Count('id')))
        total     = sum(counts.values())
        completed = counts.get('completed', 0)
        cancelled = counts.get('cancelled', 0)
        scheduled = counts.get('upcoming', 0)
        no_show   = counts.get('no_show', 0)

        rows = list(appts)
        upcoming_by_plan = {}                       # plan id → its upcoming appointments, earliest first
        for a in sorted(rows, key=lambda x: x.date_time):
            if a.price_plan_id and a.status == 'upcoming':
                upcoming_by_plan.setdefault(a.price_plan_id, []).append(a)

        timeline = []
        for a in rows:
            from django.utils import timezone as tz
            dt   = tz.localtime(a.date_time) if tz.is_aware(a.date_time) else a.date_time
            plan = a.price_plan
            next_a = next((u for u in upcoming_by_plan.get(a.price_plan_id, []) if u.date_time > a.date_time),
                          None) if plan else None

            timeline.append({
                'id':                  a.id,
                'date':                str(dt.date()),
                'treatment':           a.treatment.name if a.treatment else None,
                'therapist':           a.staff.username if a.staff else None,
                'duration':            a.duration,
                'price':               str(plan.price) if plan else str(a.payment_amount or ''),
                'package':             a.treatment.name if a.treatment and plan else None,
                'session_number':      a.session_number,
                'total_sessions':      plan.sessions if plan else a.total_sessions,
                'rating':              None,
                'next_date':           str(next_a.date_time.date()) if next_a else None,
                'status':              a.status,
                'cancellation_reason': None,
            })

        return Response({
            'stats': {
                'total':     total,
                'completed': completed,
                'cancelled': cancelled,
                'scheduled': scheduled,
                'no_show':   no_show,
            },
            'timeline': timeline,
        })


class PatientNotesView(APIView):
    """
    GET  /api/patients/<id>/notes/      — list all session notes
    POST /api/patients/<id>/notes/      — add a session note
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from patients.models import SessionNote
        patient = _get_patient(pk, request.user)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        from utils.storage import display_url
        notes       = list(SessionNote.objects.filter(patient=patient).select_related('therapist', 'appointment'))
        total       = len(notes)
        with_photos = sum(1 for n in notes if n.before_photo and n.after_photo)
        completed   = sum(1 for n in notes if n.appointment and n.appointment.status == 'completed')

        def _full_url(url):
            return display_url(url, request)

        def fmt_note(n):
            return {
                'id':                     n.id,
                'treatment_name':         n.treatment_name,
                'therapist':              n.therapist.username if n.therapist else None,
                'date':                   str(n.created_at.date()),
                'skin_observation':       n.skin_observation,
                'session_notes':          n.session_notes,
                'products_used':          n.products_used,
                'recommended_to_patient': n.recommended_to_patient,
                'next_treatment':         n.next_treatment,
                'before_photo':           _full_url(n.before_photo),
                'after_photo':            _full_url(n.after_photo),
                'appointment_status':     n.appointment.status if n.appointment else None,
            }

        return Response({
            'stats': {
                'total_notes': total,
                'completed':   completed,
                'with_photos': with_photos,
            },
            'notes': [fmt_note(n) for n in notes],
        })

    def post(self, request, pk):
        from patients.models import SessionNote
        from appointments.models import Appointment
        patient = _get_patient(pk, request.user)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        appt_id = request.data.get('appointment_id')
        appt    = None
        if appt_id:
            try:
                appt = Appointment.objects.get(id=appt_id, patient=patient)
            except Appointment.DoesNotExist:
                return Response({'error': 'Appointment not found for this patient.'}, status=404)

        from utils.image_upload import get_image_value
        from utils.storage import display_url
        note = SessionNote.objects.create(
            patient=patient,
            appointment=appt,
            therapist=request.user,
            treatment_name=request.data.get('treatment_name', appt.treatment.name if appt and appt.treatment else ''),
            skin_observation=request.data.get('skin_observation', ''),
            session_notes=request.data.get('session_notes', []),
            products_used=request.data.get('products_used', []),
            recommended_to_patient=request.data.get('recommended_to_patient', []),
            next_treatment=request.data.get('next_treatment', ''),
            before_photo=get_image_value(request, 'before_photo', folder='session_photos', prefix='before'),
            after_photo=get_image_value(request, 'after_photo', folder='session_photos', prefix='after'),
        )

        return Response({
            'id':                     note.id,
            'treatment_name':         note.treatment_name,
            'therapist':              note.therapist.username if note.therapist else None,
            'date':                   str(note.created_at.date()),
            'skin_observation':       note.skin_observation,
            'session_notes':          note.session_notes,
            'products_used':          note.products_used,
            'recommended_to_patient': note.recommended_to_patient,
            'next_treatment':         note.next_treatment,
            'before_photo':           display_url(note.before_photo, request),
            'after_photo':            display_url(note.after_photo, request),
        }, status=201)


class PatientNoteDetailView(APIView):
    """
    PATCH  /api/patients/<id>/notes/<note_id>/  — edit note
    DELETE /api/patients/<id>/notes/<note_id>/  — delete note
    """
    permission_classes = [IsAuthenticated]

    def _get_note(self, pk, note_id):
        from patients.models import SessionNote
        patient = _get_patient(pk, request.user)
        if not patient:
            return None, None
        try:
            return patient, SessionNote.objects.get(id=note_id, patient=patient)
        except SessionNote.DoesNotExist:
            return patient, None

    def patch(self, request, pk, note_id):
        patient, note = self._get_note(pk, note_id)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)
        if not note:
            return Response({'error': 'Note not found.'}, status=404)

        from utils.image_upload import get_image_value
        for field in ['skin_observation', 'session_notes', 'products_used',
                      'recommended_to_patient', 'next_treatment']:
            if field in request.data:
                setattr(note, field, request.data[field])

        if 'before_photo' in request.data or 'before_photo' in request.FILES:
            note.before_photo = get_image_value(request, 'before_photo', folder='session_photos', prefix='before')
        if 'after_photo' in request.data or 'after_photo' in request.FILES:
            note.after_photo = get_image_value(request, 'after_photo', folder='session_photos', prefix='after')

        note.save()
        return Response({'message': 'Note updated.', 'id': note.id})

    def delete(self, request, pk, note_id):
        patient, note = self._get_note(pk, note_id)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)
        if not note:
            return Response({'error': 'Note not found.'}, status=404)
        note.delete()
        return Response({'message': 'Note deleted.'})


class PatientPhotosView(APIView):
    """
    GET /api/patients/<id>/photos/
    Returns before & after photos grouped by session/treatment.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from patients.models import SessionNote
        patient = _get_patient(pk, request.user)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        notes = SessionNote.objects.filter(
            patient=patient
        ).exclude(
            before_photo='', after_photo=''
        ).select_related('therapist').order_by('-created_at')

        from utils.storage import display_url

        def _full_url_photos(url):
            return display_url(url, request)

        photos = [
            {
                'session_id':     n.id,
                'treatment_name': n.treatment_name,
                'therapist':      n.therapist.username if n.therapist else None,
                'date':           str(n.created_at.date()),
                'before_photo':   _full_url_photos(n.before_photo),
                'after_photo':    _full_url_photos(n.after_photo),
            }
            for n in notes
        ]

        return Response({'photos': photos, 'total': len(photos)})


class PatientConsentView(APIView):
    """
    GET  /api/patients/<id>/consent/
    POST /api/patients/<id>/consent/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from patients.models import ConsentRecord
        patient = _get_patient(pk, request.user)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        records = ConsentRecord.objects.filter(patient=patient, type='consent')   # other documents: /api/documents/
        signed  = records.filter(status='signed').count()
        pending = records.filter(status='pending').count()

        def fmt(r):
            return {
                'id':               r.id,
                'title':            r.title,
                'file_name':        r.file_name,
                'file_url':         r.file_url or None,
                'status':           r.status,
                'patient_signed':   r.patient_signed,
                'therapist_signed': r.therapist_signed,
                'signed_date':      str(r.signed_date) if r.signed_date else None,
                'created_at':       str(r.created_at.date()),
            }

        return Response({
            'stats':   {'signed': signed, 'pending': pending},
            'records': [fmt(r) for r in records],
        })

    def post(self, request, pk):
        from patients.models import ConsentRecord
        patient = _get_patient(pk, request.user)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        record = ConsentRecord.objects.create(
            patient=patient,
            title=request.data.get('title', ''),
            file_name=request.data.get('file_name', ''),
            file_url=request.data.get('file_url', ''),
            status=request.data.get('status', 'pending'),
            patient_signed=request.data.get('patient_signed', False),
            therapist_signed=request.data.get('therapist_signed', False),
            signed_date=request.data.get('signed_date') or None,
        )
        return Response({
            'id':               record.id,
            'title':            record.title,
            'file_name':        record.file_name,
            'status':           record.status,
            'patient_signed':   record.patient_signed,
            'therapist_signed': record.therapist_signed,
            'signed_date':      str(record.signed_date) if record.signed_date else None,
        }, status=201)


class PatientConsentDetailView(APIView):
    """
    PATCH  /api/patients/<id>/consent/<record_id>/
    DELETE /api/patients/<id>/consent/<record_id>/
    """
    permission_classes = [IsAuthenticated]

    def _get(self, request, pk, record_id):
        from patients.models import ConsentRecord
        patient = _get_patient(pk, request.user)
        if not patient:
            return None, None
        try:
            return patient, ConsentRecord.objects.get(id=record_id, patient=patient, type='consent')
        except ConsentRecord.DoesNotExist:
            return patient, None

    def patch(self, request, pk, record_id):
        patient, record = self._get(request, pk, record_id)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)
        if not record:
            return Response({'error': 'Consent record not found.'}, status=404)

        for field in ['title', 'file_name', 'file_url', 'status',
                      'patient_signed', 'therapist_signed', 'signed_date']:
            if field in request.data:
                setattr(record, field, request.data[field])
        record.save()
        return Response({'message': 'Consent record updated.', 'id': record.id})

    def delete(self, request, pk, record_id):
        patient, record = self._get(request, pk, record_id)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)
        if not record:
            return Response({'error': 'Consent record not found.'}, status=404)
        record.delete()
        return Response({'message': 'Consent record deleted.'})

class PatientFullView(APIView):
    """
    GET /api/patients/<id>/full/            everything the patient detail screen needs in one call
        ?include=patient,overview,history,notes,photos,consent,documents   (default: all)
    Each section is exactly what its own endpoint returns:
      patient   → GET /api/patients/<id>/          overview → /overview/     history → /history/
      notes     → /notes/   photos → /photos/   consent → /consent/
      documents → GET /api/documents/?patient_id=<id> (list) + counts
    Same access rules as those endpoints (therapists: only patients they can open → 404).
    """
    permission_classes = [IsAuthenticated]
    SECTIONS = ('patient', 'overview', 'history', 'notes', 'photos', 'consent', 'documents')

    def get(self, request, pk):
        from utils.api_errors import error, validation_error
        patient = _get_patient(pk, request.user)
        if not patient:
            return error(404, 'patient_not_found', 'Patient not found.')
        raw = request.query_params.get('include')
        wanted = [s.strip() for s in raw.split(',') if s.strip()] if raw else list(self.SECTIONS)
        unknown = [s for s in wanted if s not in self.SECTIONS]
        if unknown:
            return validation_error({'include': f'Unknown section(s): {", ".join(unknown)}. Use: {", ".join(self.SECTIONS)}.'})

        def run(view_cls, **kw):
            view = view_cls()
            view.request, view.args, view.kwargs, view.format_kwarg = request, (), kw, None
            return view.get(request, **kw).data

        out = {'patient_id': patient.patient_id}
        if 'patient' in wanted:
            from patients.views import PatientViewSet
            view = PatientViewSet(action='retrieve', request=request, kwargs={'pk': patient.patient_id},
                                  format_kwarg=None)
            out['patient'] = view.get_serializer(patient).data
        sections = {'overview': PatientOverviewView, 'history': PatientHistoryView, 'notes': PatientNotesView,
                    'photos': PatientPhotosView, 'consent': PatientConsentView}
        for name, cls in sections.items():
            if name in wanted:
                out[name] = run(cls, pk=patient.patient_id)
        if 'documents' in wanted:
            from patients.document_views import _visible, serialize
            from django.db.models import Case, IntegerField, Value, When
            docs = list(_visible(request).filter(patient=patient).annotate(
                _p=Case(When(status='pending', then=Value(0)), default=Value(1), output_field=IntegerField())
            ).order_by('_p', '-created_at', '-id'))
            out['documents'] = {
                'counts': {'total': len(docs),
                           'pending': sum(d.status == 'pending' for d in docs),
                           'signed': sum(d.status == 'signed' for d in docs),
                           'not_required': sum(d.status == 'not_required' for d in docs)},
                'results': [serialize(d) for d in docs],
            }
        return Response(out)