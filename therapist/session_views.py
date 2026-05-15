from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.image_utils import safe_image_url
from django.utils import timezone
import datetime


def _make_full_url(url, request):
    """Convert relative media URL to full URL."""
    if not url:
        return None
    if url.startswith('http'):
        return url
    if not url.startswith('/'):
        url = '/' + url
    return request.build_absolute_uri(url)


def _get_appointment(pk, therapist=None):
    from appointments.models import Appointment
    try:
        qs = Appointment.objects.select_related(
            'patient', 'staff', 'treatment', 'room_fk', 'price_plan'
        )
        if therapist:
            return qs.get(pk=pk, staff=therapist)
        return qs.get(pk=pk)
    except Appointment.DoesNotExist:
        return None


def _fmt_time(dt):
    from django.utils import timezone as tz
    local = tz.localtime(dt) if dt.tzinfo else dt
    return local.strftime('%I:%M %p')


def _fmt_date(dt):
    from django.utils import timezone as tz
    local = tz.localtime(dt) if dt.tzinfo else dt
    return local.strftime('%A, %b %d, %Y')


class SessionDetailView(APIView):
    """
    GET /api/therapist/sessions/<appointment_id>/
    Full session detail page for therapist.
    Returns patient info, service details, previous session recap,
    skin profile, next session info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from users.models import User as UserModel
        from appointments.models import Appointment
        from patients.models import SessionNote

        try:
            therapist = UserModel.objects.get(pk=request.user.pk)
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        appt = _get_appointment(pk, therapist)
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)

        patient   = appt.patient
        treatment = appt.treatment
        plan      = appt.price_plan
        room      = appt.room_fk

        # Previous session note for this patient + treatment
        prev_note = SessionNote.objects.filter(
            patient=patient,
            treatment_name=treatment.name if treatment else '',
        ).exclude(appointment=appt).order_by('-created_at').first()

        # This appointment's note (if already exists)
        current_note = None
        try:
            current_note = appt.session_note
        except Exception:
            pass

        # Next session in same package
        next_appt = None
        if plan:
            next_appt = Appointment.objects.filter(
                patient=patient,
                price_plan=plan,
                status='upcoming',
                date_time__gt=appt.date_time
            ).order_by('date_time').first()

        return Response({
            'appointment_id': appt.id,
            'status':         appt.status,

            # Patient info
            'patient': {
                'id':               patient.id if patient else None,
                'patient_id':       patient.patient_id if patient else None,
                'name':             patient.name if patient else None,
                'age':              _calc_age(patient.dob) if patient and patient.dob else None,
                'gender':           patient.gender if patient else None,
                'phone':            patient.phone if patient else None,
                'email':            patient.email if patient else None,
                'image':            safe_image_url(patient.image) if patient else None,
                'skin_profile': {
                    'skin_type':        patient.skin_type if patient else None,
                    'fitzpatrick':      patient.tags if patient else None,  # reuse tags for fitzpatrick
                    'allergies':        patient.allergies if patient else None,
                    'contraindications': patient.contraindications if patient else None,
                },
            },

            # Service details
            'service_details': {
                'service':        treatment.name if treatment else None,
                'package':        f"{treatment.name} Pack" if plan else None,
                'session':        f"Session {appt.session_number} of {plan.sessions if plan else appt.total_sessions}",
                'session_number': appt.session_number,
                'total_sessions': plan.sessions if plan else appt.total_sessions,
                'duration':       f"{appt.duration} mins",
                'date':           _fmt_date(appt.date_time) if appt.date_time else None,
                'time':           f"{_fmt_time(appt.date_time)} - {_fmt_end_time(appt.date_time, appt.duration)}" if appt.date_time else None,
                'room':           room.name if room else None,
            },

            # Previous session recap
            'previous_session_recap': {
                'session_number':     appt.session_number - 1 if appt.session_number > 1 else None,
                'skin_observation':   prev_note.skin_observation if prev_note else None,
                'session_notes':      prev_note.session_notes if prev_note else [],
                'products_used':      prev_note.products_used if prev_note else [],
                'note_id':            prev_note.id if prev_note else None,
            } if appt.session_number > 1 else None,

            # Current session note
            'session_note': {
                'note_id':               current_note.id if current_note else None,
                'skin_observation':      current_note.skin_observation if current_note else None,
                'session_notes':          current_note.session_notes if current_note else [],
                'products_used':         current_note.products_used if current_note else [],
                'recommended_to_patient': current_note.recommended_to_patient if current_note else [],
                'next_treatment':        current_note.next_treatment if current_note else None,
                'before_photo':          _make_full_url(current_note.before_photo, request) if current_note else None,
                'after_photo':           _make_full_url(current_note.after_photo, request) if current_note else None,
            },

            # Next session
            'next_session': {
                'appointment_id':  next_appt.id if next_appt else None,
                'label':           f"{treatment.name if treatment else ''} · Session {next_appt.session_number} of {plan.sessions if plan else ''} · {_fmt_date(next_appt.date_time)}" if next_appt else None,
            } if next_appt else None,
        })


class SessionStartView(APIView):
    """
    PATCH /api/therapist/sessions/<appointment_id>/start/
    Mark session as in-progress (patient_arrived = true).
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        from users.models import User as UserModel
        therapist = UserModel.objects.get(pk=request.user.pk)
        appt = _get_appointment(pk, therapist)
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)
        appt.patient_arrived = True
        appt.save()
        return Response({'message': 'Session started.', 'patient_arrived': True})


class SessionCompleteView(APIView):
    """
    POST /api/therapist/sessions/<appointment_id>/complete/
    Complete session — saves note, marks appointment completed.

    Body:
    {
        "skin_observation":       "Skin slightly dehydrated...",
        "session_notes":          [{"title": "Sun Exposure", "description": "Avoid sun exposure 48hrs..."}],
        "products_used":          ["Gentle Cleanser", "Hyaluronic Acid Serum"],
        "recommended_to_patient": ["Hydrating Serum", "SPF 50+"],
        "next_treatment":         "HydraBalance — in 2-3 weeks",
        "before_photo":           "https://...",
        "after_photo":            "https://...",
        "therapist_note_for_next": "Focus on dehydrated area next session"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from users.models import User as UserModel
        from patients.models import SessionNote
        therapist = UserModel.objects.get(pk=request.user.pk)
        appt = _get_appointment(pk, therapist)
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)

        if appt.status == 'completed':
            return Response({'error': 'Session already completed.'}, status=400)

        # Handle image uploads (supports both file upload and URL)
        from utils.image_upload import get_image_value
        before_photo = get_image_value(request, 'before_photo', folder='session_photos', prefix='before')
        after_photo  = get_image_value(request, 'after_photo',  folder='session_photos', prefix='after')

        # Save or update session note
        note_data = {
            'patient':                appt.patient,
            'appointment':            appt,
            'therapist':              therapist,
            'treatment_name':         appt.treatment.name if appt.treatment else '',
            'skin_observation':       request.data.get('skin_observation', ''),
            'session_notes':          request.data.get('session_notes', []),
            'products_used':          request.data.get('products_used', []),
            'recommended_to_patient': request.data.get('recommended_to_patient', []),
            'next_treatment':         request.data.get('next_treatment', ''),
            'before_photo':           before_photo,
            'after_photo':            after_photo,
        }

        try:
            note = appt.session_note
            for k, v in note_data.items():
                setattr(note, k, v)
            note.save()
        except SessionNote.DoesNotExist:
            note = SessionNote.objects.create(**note_data)
        except Exception:
            note = SessionNote.objects.create(**note_data)

        # Mark appointment completed
        appt.status = 'completed'
        appt.save()

        # Auto-update patient category
        from appointments.views import _update_patient_category
        _update_patient_category(appt.patient)

        return Response({
            'message':    'Session completed successfully.',
            'note_id':    note.id,
            'appointment_id': appt.id,
            'status':     'completed',
        })


class SessionNoteUpdateView(APIView):
    """
    PATCH /api/therapist/sessions/<appointment_id>/note/
    Update session note fields individually (skin observation, photos, products etc).

    Body (all optional):
    {
        "skin_observation":       "Updated observation",
        "session_notes":          [{"title": "Updated", "description": "Updated advice"}],
        "products_used":          ["Product A"],
        "recommended_to_patient": ["Product B"],
        "next_treatment":         "Next treatment info",
        "before_photo":           "https://...",
        "after_photo":            "https://..."
    }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        from users.models import User as UserModel
        from patients.models import SessionNote
        therapist = UserModel.objects.get(pk=request.user.pk)
        appt = _get_appointment(pk, therapist)
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)

        try:
            note = appt.session_note
        except Exception:
            note = SessionNote.objects.create(
                patient=appt.patient,
                appointment=appt,
                therapist=therapist,
                treatment_name=appt.treatment.name if appt.treatment else '',
            )

        from utils.image_upload import get_image_value
        fields = ['skin_observation', 'session_notes', 'products_used',
                  'recommended_to_patient', 'next_treatment']
        for field in fields:
            if field in request.data:
                setattr(note, field, request.data[field])

        # Handle photo uploads
        if 'before_photo' in request.data or 'before_photo' in request.FILES:
            note.before_photo = get_image_value(request, 'before_photo', folder='session_photos', prefix='before')
        if 'after_photo' in request.data or 'after_photo' in request.FILES:
            note.after_photo = get_image_value(request, 'after_photo', folder='session_photos', prefix='after')

        note.save()

        return Response({
            'message':               'Note updated.',
            'note_id':               note.id,
            'skin_observation':      note.skin_observation,
            'session_notes':         note.session_notes,
            'products_used':         note.products_used,
            'recommended_to_patient': note.recommended_to_patient,
            'next_treatment':        note.next_treatment,
            'before_photo':          _make_full_url(note.before_photo, request) or None,
            'after_photo':           _make_full_url(note.after_photo, request) or None,
        })


def _calc_age(dob):
    if not dob:
        return None
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _fmt_end_time(dt, duration):
    from django.utils import timezone as tz
    local = tz.localtime(dt) if dt.tzinfo else dt
    end   = local + datetime.timedelta(minutes=duration or 0)
    return end.strftime('%I:%M %p')