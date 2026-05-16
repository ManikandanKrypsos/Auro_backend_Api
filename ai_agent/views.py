from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import json
import requests


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def _get_clinic_context(user):
    """Build real clinic data context based on user role."""
    from appointments.models import Appointment
    from patients.models import Patient
    from users.models import User as UserModel
    from leads.models import Lead
    from inventory.models import InventoryItem

    today = timezone.localdate()
    now   = timezone.now()
    role  = getattr(user, 'role', '') or ''
    name  = user.username or user.email.split('@')[0]

    context = {
        'role':  role,
        'name':  name,
        'today': str(today),
    }

    if role == 'therapist':
        todays_appts = Appointment.objects.filter(
            staff=user, date_time__date=today
        ).select_related('patient', 'treatment', 'room_fk')
        context['my_schedule_today'] = [
            {
                'time':            a.date_time.strftime('%H:%M') if a.date_time else None,
                'patient':         a.patient.name if a.patient else None,
                'patient_id':      a.patient.patient_id if a.patient else None,
                'patient_phone':   a.patient.phone if a.patient else None,
                'treatment':       a.treatment.name if a.treatment else None,
                'status':          a.status,
                'duration':        a.duration,
                'room':            a.room_fk.name if a.room_fk else None,
                'session':         f"Session {a.session_number} of {a.total_sessions}",
            }
            for a in todays_appts.order_by('date_time')
        ]
        context['total_today']       = todays_appts.count()
        context['completed_today']   = todays_appts.filter(status='completed').count()
        context['pending_today']      = todays_appts.filter(status='upcoming').count()
        context['in_session']         = todays_appts.filter(status='in_session').count()
        context['my_patients_count']  = Appointment.objects.filter(staff=user).values('patient').distinct().count()
        from patients.models import Patient as PatientModel
        patient_ids = Appointment.objects.filter(staff=user).values_list('patient_id', flat=True).distinct()
        context['my_patients'] = [
            {'id': p.patient_id, 'name': p.name, 'phone': p.phone, 'email': p.email,
             'gender': p.gender, 'category': p.category, 'allergies': p.allergies, 'skin_type': p.skin_type}
            for p in PatientModel.objects.filter(id__in=patient_ids).order_by('-created_at')[:20]
        ]

    elif role == 'reception':
        todays_appts = Appointment.objects.filter(date_time__date=today)
        context['todays_appointments'] = todays_appts.count()
        context['checked_in']          = todays_appts.filter(patient_arrived=True).count()
        context['cancelled_today']      = todays_appts.filter(status='cancelled').count()
        context['in_session_today']     = todays_appts.filter(status='in_session').count()
        context['total_patients']       = Patient.objects.count()
        context['new_patients_month']   = Patient.objects.filter(created_at__gte=now.replace(day=1)).count()
        context['active_leads']         = Lead.objects.filter(stage__in=['new_inquiries','engaged','consultation','winning']).count()
        context['todays_schedule'] = [
            {'time': a.date_time.strftime('%H:%M') if a.date_time else None,
             'patient': a.patient.name if a.patient else None,
             'treatment': a.treatment.name if a.treatment else None,
             'therapist': a.staff.username if a.staff else None,
             'status': a.status}
            for a in todays_appts.select_related('patient','treatment','staff').order_by('date_time')
        ]
        context['recent_leads'] = [
            {'name': l.name, 'phone': l.phone, 'stage': l.stage}
            for l in Lead.objects.order_by('-created_at')[:5]
        ]
        context['patients'] = [
            {'id': p.patient_id, 'name': p.name, 'phone': p.phone, 'email': p.email,
             'gender': p.gender, 'category': p.category, 'allergies': p.allergies}
            for p in Patient.objects.all().order_by('-created_at')[:20]
        ]

    else:
        from django.db.models import Sum, Count
        from treatments.models import Treatment
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        todays_appts   = Appointment.objects.filter(date_time__date=today)
        month_appts    = Appointment.objects.filter(date_time__gte=start_of_month)
        context['todays_appointments']  = todays_appts.count()
        context['monthly_appointments'] = month_appts.count()
        context['total_patients']       = Patient.objects.count()
        context['active_leads']         = Lead.objects.filter(stage__in=['new_inquiries','engaged','consultation','winning']).count()
        context['total_leads']          = Lead.objects.count()
        context['revenue_this_month']   = float(month_appts.filter(status='completed').aggregate(t=Sum('payment_amount'))['t'] or 0)
        context['low_stock_items']      = InventoryItem.objects.filter(current_stock__lte=10).count()
        staff_list = UserModel.objects.filter(role__in=['therapist','reception'], is_active=True).values('id','username','email','phone','role','specialist_area')
        context['total_staff']  = len(list(staff_list))
        context['staff_list']   = [{'id': s['id'], 'name': s['username'] or s['email'].split('@')[0], 'role': s['role'], 'email': s['email'], 'phone': s['phone'], 'specialist_area': s['specialist_area']} for s in staff_list]
        context['todays_schedule'] = [{'time': a.date_time.strftime('%H:%M') if a.date_time else None, 'patient': a.patient.name if a.patient else None, 'treatment': a.treatment.name if a.treatment else None, 'therapist': a.staff.username if a.staff else None, 'status': a.status} for a in todays_appts.select_related('patient','treatment','staff').order_by('date_time')]
        therapist_stats = []
        for s in UserModel.objects.filter(role='therapist', is_active=True):
            sa = Appointment.objects.filter(staff=s, date_time__gte=start_of_month)
            therapist_stats.append({'name': s.username or s.email.split('@')[0], 'sessions': sa.count(), 'completed': sa.filter(status='completed').count(), 'revenue': float(sa.filter(status='completed').aggregate(t=Sum('payment_amount'))['t'] or 0)})
        therapist_stats.sort(key=lambda x: x['revenue'], reverse=True)
        context['therapist_performance'] = therapist_stats
        context['recent_leads'] = [{'name': l.name, 'phone': l.phone, 'source': l.source, 'stage': l.stage, 'value': str(l.value)} for l in Lead.objects.order_by('-created_at')[:5]]
        context['patient_categories'] = {'new': Patient.objects.filter(category='New').count(), 'returning': Patient.objects.filter(category='Returning').count(), 'vip': Patient.objects.filter(category='VIP').count()}
        context['patients'] = [{'id': p.patient_id, 'name': p.name, 'phone': p.phone, 'email': p.email, 'gender': p.gender, 'category': p.category, 'allergies': p.allergies} for p in Patient.objects.all().order_by('-created_at')[:20]]
        context['low_stock_details'] = [{'name': i.name, 'current_stock': i.current_stock, 'minimum_stock': i.minimum_stock_alert, 'unit': i.unit} for i in InventoryItem.objects.filter(current_stock__lte=10)[:10]]
        context['top_services'] = [{'treatment': s['treatment__name'], 'bookings': s['count']} for s in Appointment.objects.filter(date_time__gte=start_of_month).values('treatment__name').annotate(count=Count('id')).order_by('-count')[:5]]

    return context


def _build_system_prompt(user, context):
    """Build role-specific system prompt with clinic data and booking capability."""
    role = context.get('role', '')
    name = context.get('name', '')

    base = f"""You are AURA AI, an intelligent assistant for Aura Clinic management system.
You are currently talking to {name}, who is a {role}.
Today's date is {context.get('today')}.

You have access to real-time clinic data provided below.
Be concise, helpful and professional. Use the data to give accurate answers.
Never make up patient names, appointment times or financial figures.

CURRENT CLINIC DATA:
{json.dumps(context, indent=2)}

---
BOOKING APPOINTMENTS CAPABILITY:
You can help book appointments by collecting required information step by step.
When user wants to book an appointment, follow this exact flow:

STEP 1 - Ask for patient (search by name or ID from patients list above)
STEP 2 - Ask for treatment/service
STEP 3 - Ask for therapist (show available therapists)
STEP 4 - Ask for preferred date
STEP 5 - Call available slots and show options (you will receive slot data)
STEP 6 - Ask which time slot they want
STEP 7 - Ask for room (if not auto-selected)
STEP 8 - Confirm all details before booking
STEP 9 - Return action: BOOK_APPOINTMENT with all collected data

When you have collected ALL required information and user confirms, respond with this EXACT format at the END of your message:
ACTION:BOOK_APPOINTMENT:{{"patient_id":"<id>","staff_id":<id>,"treatment_id":<id>,"room_id":<id>,"price_plan_id":<id>,"date":"YYYY-MM-DD","time":"HH:MM"}}

When you need to check available slots, respond with:
ACTION:GET_SLOTS:{{"staff_id":<id>,"service_id":<id>,"month":"YYYY-MM","room_id":<id>}}

When you need to get treatments list, respond with:
ACTION:GET_TREATMENTS:{{}}

When you need to get rooms list, respond with:
ACTION:GET_ROOMS:{{}}

Important rules for booking:
- Always confirm with user before final booking
- Show a clear summary before booking
- patient_id should be the numeric DB id (not Aura49 format)
- If patient not found in list, ask them to check the name
"""

    if role == 'therapist':
        base += "\nYou can help therapists book follow-up appointments for their patients."
    elif role == 'reception':
        base += "\nYou assist reception with booking appointments for patients."
    else:
        base += "\nAs admin you have full access to book and manage appointments."

    return base


def _execute_action(action_str, token):
    """Execute an action returned by AI — calls backend APIs."""
    import re
    base_url = "https://auro-backend-api.onrender.com/api"
    headers  = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if action_str.startswith("ACTION:GET_TREATMENTS:"):
            resp = requests.get(f"{base_url}/treatments/", headers=headers, timeout=10)
            treatments = resp.json()
            return {
                'action':     'GET_TREATMENTS',
                'data':       [{'id': t['id'], 'name': t['name'], 'duration': t['duration'],
                                'price_plans': t.get('price_plans', [])} for t in treatments],
                'message':    'Here are the available treatments:'
            }

        elif action_str.startswith("ACTION:GET_ROOMS:"):
            resp = requests.get(f"{base_url}/rooms/", headers=headers, timeout=10)
            rooms = resp.json()
            return {
                'action':  'GET_ROOMS',
                'data':    rooms,
                'message': 'Here are the available rooms:'
            }

        elif action_str.startswith("ACTION:GET_SLOTS:"):
            params_str = action_str.split("ACTION:GET_SLOTS:")[1]
            params     = json.loads(params_str)
            resp = requests.get(
                f"{base_url}/appointments/available-slots/",
                params=params,
                headers=headers,
                timeout=10
            )
            return {
                'action':  'GET_SLOTS',
                'data':    resp.json(),
                'message': 'Here are the available slots:'
            }

        elif action_str.startswith("ACTION:BOOK_APPOINTMENT:"):
            params_str = action_str.split("ACTION:BOOK_APPOINTMENT:")[1]
            body       = json.loads(params_str)
            resp = requests.post(
                f"{base_url}/appointments/",
                json=body,
                headers=headers,
                timeout=10
            )
            if resp.status_code == 201:
                appt = resp.json()
                return {
                    'action':  'BOOK_APPOINTMENT',
                    'success': True,
                    'data':    appt,
                    'message': f"✅ Appointment booked successfully! ID: {appt.get('id')}"
                }
            else:
                return {
                    'action':  'BOOK_APPOINTMENT',
                    'success': False,
                    'data':    resp.json(),
                    'message': f"❌ Booking failed: {resp.json()}"
                }

    except Exception as e:
        return {'action': 'ERROR', 'message': str(e)}

    return None


class AIChatView(APIView):
    """
    POST /api/ai/chat/
    Chat with the Aura AI agent. Supports booking appointments conversationally.

    Body:
    {
        "message": "I want to book an appointment",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"}
        ],
        "auth_token": "Bearer eyJ..."   // pass JWT token for booking actions
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from users.models import User as UserModel

        message  = request.data.get('message', '').strip()
        history  = request.data.get('conversation_history', [])
        # Get auth token for action execution
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = auth_header.replace('Bearer ', '').strip()

        if not message:
            return Response({'error': 'message is required.'}, status=400)

        try:
            user = UserModel.objects.get(pk=request.user.pk)
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        try:
            context = _get_clinic_context(user)
        except Exception as e:
            context = {'role': getattr(user, 'role', ''), 'name': user.username, 'today': str(timezone.localdate())}

        system_prompt = _build_system_prompt(user, context)

        # Build Gemini messages
        gemini_contents = []
        for h in history:
            if h.get('role') == 'user':
                gemini_contents.append({'role': 'user', 'parts': [{'text': h['content']}]})
            elif h.get('role') == 'assistant':
                gemini_contents.append({'role': 'model', 'parts': [{'text': h['content']}]})

        full_message = f"{system_prompt}\n\nUser message: {message}"
        gemini_contents.append({'role': 'user', 'parts': [{'text': full_message}]})

        try:
            import os
            api_key = os.environ.get('GEMINI_API_KEY', '')
            if not api_key:
                return Response({'error': 'AI service not configured. Please contact admin.'}, status=503)

            response = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                headers={'Content-Type': 'application/json'},
                json={'contents': gemini_contents},
                timeout=30,
            )

            if response.status_code != 200:
                return Response({'error': 'AI service error. Please try again.', 'detail': response.text}, status=503)

            data  = response.json()
            reply = data['candidates'][0]['content']['parts'][0]['text']

            # Check if AI returned an action
            action_result = None
            action_line   = None

            for line in reply.split('\n'):
                if line.strip().startswith('ACTION:'):
                    action_line = line.strip()
                    break

            if action_line and token:
                action_result = _execute_action(action_line, token)
                # Remove action line from reply shown to user
                reply = reply.replace(action_line, '').strip()

                # If action was GET_SLOTS or GET_TREATMENTS, feed result back to AI
                if action_result and action_result.get('action') in ['GET_SLOTS', 'GET_TREATMENTS', 'GET_ROOMS']:
                    follow_up = f"Here is the data you requested:\n{json.dumps(action_result['data'], indent=2)}\n\nNow present this to the user in a friendly way and ask them to choose."
                    gemini_contents.append({'role': 'model', 'parts': [{'text': reply}]})
                    gemini_contents.append({'role': 'user', 'parts': [{'text': follow_up}]})

                    response2 = requests.post(
                        f"{GEMINI_API_URL}?key={api_key}",
                        headers={'Content-Type': 'application/json'},
                        json={'contents': gemini_contents},
                        timeout=30,
                    )
                    if response2.status_code == 200:
                        data2  = response2.json()
                        reply  = data2['candidates'][0]['content']['parts'][0]['text']

            return Response({
                'reply':         reply,
                'role':          context.get('role'),
                'action_result': action_result,
                'context': {
                    'name':  context.get('name'),
                    'today': context.get('today'),
                },
            })

        except requests.Timeout:
            return Response({'error': 'AI response timed out. Please try again.'}, status=504)
        except Exception as e:
            return Response({'error': f'AI service error: {str(e)}'}, status=503)