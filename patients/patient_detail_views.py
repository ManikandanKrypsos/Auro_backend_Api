# Add these views to patients/views.py (or a separate file and include in urls)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminOrReception
from django.utils import timezone
from django.db.models import Count, Q
import datetime


def _get_patient(pk):
    from patients.models import Patient
    try:
        if str(pk).isdigit():
            return Patient.objects.get(id=int(pk))
        return Patient.objects.get(patient_id__iexact=pk)
    except Patient.DoesNotExist:
        return None


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

        patient = _get_patient(pk)
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

        # Active packages — appointments with price_plan grouped by plan
        from treatments.models import PricePlan
        active_packages = []
        plan_ids = Appointment.objects.filter(
            patient=patient,
            price_plan__isnull=False
        ).values_list('price_plan_id', flat=True).distinct()

        for plan_id in plan_ids:
            appts_in_plan = Appointment.objects.filter(
                patient=patient,
                price_plan_id=plan_id
            ).select_related('price_plan', 'treatment', 'staff').order_by('date_time')
            if not appts_in_plan.exists():
                continue
            first = appts_in_plan.first()
            plan  = first.price_plan
            completed = appts_in_plan.filter(status='completed').count()
            next_a    = appts_in_plan.filter(status='upcoming', date_time__gte=now).order_by('date_time').first()
            active_packages.append({
                'plan_id':       plan_id,
                'package_name':  first.treatment.name if first.treatment else '',
                'therapist':     first.staff.username if first.staff else None,
                'sessions_used': completed,
                'total_sessions': plan.sessions if plan else first.total_sessions,
                'next_date':     str(next_a.date_time.date()) if next_a else None,
            })

        # Patient activity timeline
        activity = []

        # Completed appointments
        for a in Appointment.objects.filter(
            patient=patient
        ).select_related('staff', 'treatment', 'price_plan').order_by('-date_time')[:20]:
            from django.utils import timezone as tz
            dt = tz.localtime(a.date_time) if tz.is_aware(a.date_time) else a.date_time
            plan = a.price_plan
            activity.append({
                'type':     'treatment',
                'date':     str(dt.date()),
                'title':    f"{a.treatment.name if a.treatment else 'Treatment'} — Session {a.session_number} of {plan.sessions if plan else a.total_sessions}",
                'subtitle': f"{a.staff.username if a.staff else ''} · {a.duration} min · ${a.payment_amount or ''}",
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

        # Payments
        for a in Appointment.objects.filter(
            patient=patient,
            payment_status='paid',
            payment_amount__isnull=False
        ).select_related('price_plan').order_by('-date_time')[:5]:
            from django.utils import timezone as tz
            dt = tz.localtime(a.date_time) if tz.is_aware(a.date_time) else a.date_time
            plan = a.price_plan
            activity.append({
                'type':     'payment',
                'date':     str(dt.date()),
                'title':    'Payment Received',
                'subtitle': f"${a.payment_amount} · {a.treatment.name if a.treatment else ''} · {plan.sessions if plan else ''} Sessions",
            })

        # Sort by date desc
        activity.sort(key=lambda x: x['date'], reverse=True)

        return Response({
            'patient_id':      patient.patient_id,
            'name':            patient.name,
            'category':        patient.category,
            'allergy_warning': patient.allergies if hasattr(patient, 'allergies') else None,
            'upcoming_appointment': fmt_appt(next_appt),
            'active_packages': active_packages,
            'patient_activity': activity[:15],
        })


class PatientHistoryView(APIView):
    """
    GET /api/patients/<id>/history/
    Returns treatment timeline with stats: total, completed, cancelled, scheduled.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from appointments.models import Appointment
        patient = _get_patient(pk)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        appts = Appointment.objects.filter(
            patient=patient
        ).select_related('staff', 'treatment', 'room_fk', 'price_plan').order_by('-date_time')

        total     = appts.count()
        completed = appts.filter(status='completed').count()
        cancelled = appts.filter(status='cancelled').count()
        scheduled = appts.filter(status='upcoming').count()

        timeline = []
        for a in appts:
            from django.utils import timezone as tz
            dt   = tz.localtime(a.date_time) if tz.is_aware(a.date_time) else a.date_time
            plan = a.price_plan
            next_a = Appointment.objects.filter(
                patient=patient,
                price_plan=plan,
                status='upcoming',
                date_time__gt=a.date_time
            ).order_by('date_time').first() if plan else None

            timeline.append({
                'id':             a.id,
                'date':           str(dt.date()),
                'treatment':      a.treatment.name if a.treatment else None,
                'therapist':      a.staff.username if a.staff else None,
                'duration':       a.duration,
                'price':          str(plan.price) if plan else str(a.payment_amount or ''),
                'package':        a.treatment.name if a.treatment and plan else None,
                'session_number': a.session_number,
                'total_sessions': plan.sessions if plan else a.total_sessions,
                'rating':         None,
                'next_date':      str(next_a.date_time.date()) if next_a else None,
                'status':         a.status,
                'cancellation_reason': None,
            })

        return Response({
            'stats': {
                'total':     total,
                'completed': completed,
                'cancelled': cancelled,
                'scheduled': scheduled,
            },
            'timeline': timeline,
        })


class PatientNotesView(APIView):
    """
    GET  /api/patients/<id>/notes/      — list all session notes
    POST /api/patients/<id>/notes/      — add a session note

    POST body:
    {
        "appointment_id":        25,
        "treatment_name":        "Detox Face",
        "skin_observation":      "Skin slightly dehydrated on T-zone.",
        "advice_given":          "Avoid sun exposure for 48 hours.",
        "products_used":         ["Gentle Cleanser", "Hyaluronic Acid Serum"],
        "recommended_to_patient": ["Hydrating Serum", "SPF 50+"],
        "next_treatment":        "HydraBalance — in 2-3 weeks",
        "before_photo":          "https://...",
        "after_photo":           "https://..."
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from patients.models import SessionNote
        patient = _get_patient(pk)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        notes = SessionNote.objects.filter(patient=patient).select_related('therapist')
        total       = notes.count()
        with_photos = notes.exclude(before_photo='').exclude(after_photo='').count()
        completed   = notes.filter(appointment__status='completed').count()

        def fmt_note(n):
            return {
                'id':                    n.id,
                'treatment_name':        n.treatment_name,
                'therapist':             n.therapist.username if n.therapist else None,
                'date':                  str(n.created_at.date()),
                'skin_observation':      n.skin_observation,
                'advice_given':          n.advice_given,
                'products_used':         n.products_used,
                'recommended_to_patient': n.recommended_to_patient,
                'next_treatment':        n.next_treatment,
                'before_photo':          n.before_photo or None,
                'after_photo':           n.after_photo or None,
                'appointment_status':    n.appointment.status if n.appointment else None,
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
        patient = _get_patient(pk)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        appt_id = request.data.get('appointment_id')
        appt    = None
        if appt_id:
            try:
                appt = Appointment.objects.get(id=appt_id, patient=patient)
            except Appointment.DoesNotExist:
                return Response({'error': 'Appointment not found for this patient.'}, status=404)

        note = SessionNote.objects.create(
            patient=patient,
            appointment=appt,
            therapist=request.user,
            treatment_name=request.data.get('treatment_name', appt.treatment.name if appt and appt.treatment else ''),
            skin_observation=request.data.get('skin_observation', ''),
            advice_given=request.data.get('advice_given', ''),
            products_used=request.data.get('products_used', []),
            recommended_to_patient=request.data.get('recommended_to_patient', []),
            next_treatment=request.data.get('next_treatment', ''),
            before_photo=request.data.get('before_photo', ''),
            after_photo=request.data.get('after_photo', ''),
        )

        return Response({
            'id':                    note.id,
            'treatment_name':        note.treatment_name,
            'therapist':             note.therapist.username if note.therapist else None,
            'date':                  str(note.created_at.date()),
            'skin_observation':      note.skin_observation,
            'advice_given':          note.advice_given,
            'products_used':         note.products_used,
            'recommended_to_patient': note.recommended_to_patient,
            'next_treatment':        note.next_treatment,
            'before_photo':          note.before_photo or None,
            'after_photo':           note.after_photo or None,
        }, status=201)


class PatientNoteDetailView(APIView):
    """
    PATCH  /api/patients/<id>/notes/<note_id>/  — edit note
    DELETE /api/patients/<id>/notes/<note_id>/  — delete note
    """
    permission_classes = [IsAuthenticated]

    def _get_note(self, pk, note_id):
        from patients.models import SessionNote
        patient = _get_patient(pk)
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

        for field in ['skin_observation', 'advice_given', 'products_used',
                      'recommended_to_patient', 'next_treatment', 'before_photo', 'after_photo']:
            if field in request.data:
                setattr(note, field, request.data[field])
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
        patient = _get_patient(pk)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        notes = SessionNote.objects.filter(
            patient=patient
        ).exclude(
            before_photo='', after_photo=''
        ).select_related('therapist').order_by('-created_at')

        photos = [
            {
                'session_id':     n.id,
                'treatment_name': n.treatment_name,
                'therapist':      n.therapist.username if n.therapist else None,
                'date':           str(n.created_at.date()),
                'before_photo':   n.before_photo or None,
                'after_photo':    n.after_photo or None,
            }
            for n in notes
        ]

        return Response({'photos': photos, 'total': len(photos)})


class PatientConsentView(APIView):
    """
    GET  /api/patients/<id>/consent/     — list consent records
    POST /api/patients/<id>/consent/     — add consent record

    POST body:
    {
        "title":            "General Treatment Consent",
        "file_name":        "general_consent_jan25.pdf",
        "file_url":         "https://...",
        "status":           "signed",         // signed | pending
        "patient_signed":   true,
        "therapist_signed": true,
        "signed_date":      "2025-01-12"
    }
    """
    permission_classes = [IsAdminOrReception]

    def get(self, request, pk):
        from patients.models import ConsentRecord
        patient = _get_patient(pk)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        records = ConsentRecord.objects.filter(patient=patient)
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
        patient = _get_patient(pk)
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
    PATCH  /api/patients/<id>/consent/<record_id>/  — update consent
    DELETE /api/patients/<id>/consent/<record_id>/  — delete consent
    """
    permission_classes = [IsAdminOrReception]

    def _get(self, pk, record_id):
        from patients.models import ConsentRecord
        patient = _get_patient(pk)
        if not patient:
            return None, None
        try:
            return patient, ConsentRecord.objects.get(id=record_id, patient=patient)
        except ConsentRecord.DoesNotExist:
            return patient, None

    def patch(self, request, pk, record_id):
        patient, record = self._get(pk, record_id)
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
        patient, record = self._get(pk, record_id)
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)
        if not record:
            return Response({'error': 'Consent record not found.'}, status=404)
        record.delete()
        return Response({'message': 'Consent record deleted.'})