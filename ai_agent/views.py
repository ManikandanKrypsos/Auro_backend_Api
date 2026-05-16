from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import json
import requests
import os


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"  # free, fast


def _get_clinic_context(user):
    from appointments.models import Appointment
    from patients.models import Patient
    from users.models import User as UserModel
    from leads.models import Lead
    from inventory.models import InventoryItem
    from treatments.models import Treatment
    from rooms.models import Room

    today = timezone.localdate()
    now   = timezone.now()
    role  = getattr(user, 'role', '') or ''
    name  = user.username or user.email.split('@')[0]

    context = {
        'role':  role,
        'name':  name,
        'today': str(today),
    }

    # Always include booking data
    context['patients'] = [
        {'db_id': p.id, 'patient_id': p.patient_id, 'name': p.name, 'phone': p.phone, 'category': p.category}
        for p in Patient.objects.all().order_by('name')[:50]
    ]
    context['therapists'] = [
        {'id': s.id, 'name': s.username or s.email.split('@')[0], 'specialist_area': s.specialist_area}
        for s in UserModel.objects.filter(role='therapist', is_active=True).order_by('username')
    ]
    context['treatments'] = [
        {
            'id':          t.id,
            'name':        t.name,
            'duration':    t.duration,
            'category':    t.category,
            'price_plans': [{'id': p.id, 'sessions': p.sessions, 'price': str(p.price)} for p in t.price_plans.all()],
        }
        for t in Treatment.objects.prefetch_related('price_plans').all()
    ]
    context['rooms'] = [
        {'id': r.id, 'name': r.name, 'room_type': r.room_type}
        for r in Room.objects.all()
    ]

    # Role specific context
    if role == 'therapist':
        todays_appts = Appointment.objects.filter(staff=user, date_time__date=today).select_related('patient', 'treatment', 'room_fk')
        context['my_schedule_today'] = [
            {'time': a.date_time.strftime('%H:%M') if a.date_time else None, 'patient': a.patient.name if a.patient else None,
             'treatment': a.treatment.name if a.treatment else None, 'status': a.status, 'appointment_id': a.id}
            for a in todays_appts.order_by('date_time')
        ]
        context['total_today']     = todays_appts.count()
        context['completed_today'] = todays_appts.filter(status='completed').count()

    elif role == 'reception':
        todays_appts = Appointment.objects.filter(date_time__date=today)
        context['todays_appointments'] = todays_appts.count()
        context['checked_in']          = todays_appts.filter(patient_arrived=True).count()
        context['cancelled_today']      = todays_appts.filter(status='cancelled').count()
        context['in_session_today']     = todays_appts.filter(status='in_session').count()
        context['todays_schedule'] = [
            {'appointment_id': a.id, 'time': a.date_time.strftime('%H:%M') if a.date_time else None,
             'patient': a.patient.name if a.patient else None, 'treatment': a.treatment.name if a.treatment else None,
             'therapist': a.staff.username if a.staff else None, 'status': a.status}
            for a in todays_appts.select_related('patient', 'treatment', 'staff').order_by('date_time')
        ]

    else:
        from django.db.models import Sum, Count
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        todays_appts   = Appointment.objects.filter(date_time__date=today)
        month_appts    = Appointment.objects.filter(date_time__gte=start_of_month)
        context['todays_appointments']  = todays_appts.count()
        context['monthly_appointments'] = month_appts.count()
        context['revenue_this_month']   = float(month_appts.filter(status='completed').aggregate(t=Sum('payment_amount'))['t'] or 0)
        context['todays_schedule'] = [
            {'appointment_id': a.id, 'time': a.date_time.strftime('%H:%M') if a.date_time else None,
             'patient': a.patient.name if a.patient else None, 'treatment': a.treatment.name if a.treatment else None,
             'therapist': a.staff.username if a.staff else None, 'status': a.status}
            for a in todays_appts.select_related('patient', 'treatment', 'staff').order_by('date_time')
        ]

    return context


def _build_system_prompt(user, context):
    role = context.get('role', '')
    name = context.get('name', '')

    # Build readable lists for AI to use
    patients_list  = '\n'.join([f"  {i+1}. {p['name']} (ID: {p['patient_id']}, db_id: {p['db_id']})" for i, p in enumerate(context.get('patients', []))])
    therapists_list = '\n'.join([f"  {i+1}. {t['name']} (id: {t['id']}) - {t['specialist_area']}" for i, t in enumerate(context.get('therapists', []))])
    treatments_list = '\n'.join([f"  {i+1}. {t['name']} (id: {t['id']}, {t['duration']} min, category: {t['category']})" for i, t in enumerate(context.get('treatments', []))])
    rooms_list      = '\n'.join([f"  {i+1}. {r['name']} (id: {r['id']}, type: {r['room_type']})" for i, r in enumerate(context.get('rooms', []))])

    return f"""You are AURA AI, an intelligent assistant for Aura Clinic.
You are talking to {name}, who is a {role}. Today is {context.get('today')}.

CLINIC DATA:
{json.dumps({k: v for k, v in context.items() if k not in ['patients', 'therapists', 'treatments', 'rooms']}, indent=2)}

AVAILABLE PATIENTS:
{patients_list}

AVAILABLE THERAPISTS:
{therapists_list}

AVAILABLE TREATMENTS:
{treatments_list}

AVAILABLE ROOMS:
{rooms_list}

===== APPOINTMENT BOOKING FLOW =====
When user wants to BOOK an appointment, first check if they already provided some details.
If patient/treatment/therapist/room already mentioned — extract and skip those steps.

STEPS (skip any step where info already provided):
STEP 1: If patient not given → respond with JSON block at end:
SHOW_OPTIONS:{{"type":"patient","question":"Which patient would you like to book for?","options":[{{"id":<db_id>,"label":"<name>","subtitle":"<patient_id>"}},...]}}

STEP 2: If treatment not given → respond with:
SHOW_OPTIONS:{{"type":"treatment","question":"Which treatment?","options":[{{"id":<id>,"label":"<name>","subtitle":"<duration> min"}},...]}}

STEP 3: If therapist not given → respond with:
SHOW_OPTIONS:{{"type":"therapist","question":"Which therapist?","options":[{{"id":<id>,"label":"<name>","subtitle":"<specialist_area>"}},...]}}

STEP 4: If room not given → respond with:
SHOW_OPTIONS:{{"type":"room","question":"Which room?","options":[{{"id":<id>,"label":"<name>","subtitle":"<room_type>"}},...]}}

STEP 5: If date not given → First fetch available slots for the month:
ACTION:GET_SLOTS:{{"staff_id":<id>,"service_id":<id>,"month":"YYYY-MM","room_id":<id>}}

STEP 6: After getting slots data → Extract dates that have available time slots (is_working_day=true and has unblocked times).
Show those dates as options:
SHOW_OPTIONS:{{"type":"date","question":"Which date would you like?","options":[{{"id":"YYYY-MM-DD","label":"Mon, 20 May 2026","subtitle":"X slots available"}},...]}}
If no dates available say "No available dates this month for this therapist."

STEP 7: After date selected → Show available time slots for that specific date only:
SHOW_OPTIONS:{{"type":"slot","question":"Which time slot?","options":[{{"id":"HH:MM","label":"10:30 AM","subtitle":"available"}},...]}}
If no slots available for that date say "No available slots on this date. Please choose another date."
SHOW_OPTIONS:{{"type":"confirm","question":"Confirm this booking?","options":[{{"id":"yes","label":"✅ Confirm"}},{{"id":"no","label":"❌ Cancel"}}],"summary":{{"patient":"<name>","treatment":"<name>","therapist":"<name>","room":"<name>","date":"<date>","time":"<time>"}}}}

STEP 9: If confirmed →
ACTION:BOOK_APPOINTMENT:{{"patient_id":<db_id>,"staff_id":<id>,"treatment_id":<id>,"room_id":<id>,"price_plan_id":<id>,"date":"YYYY-MM-DD","time":"HH:MM"}}

===== CANCEL APPOINTMENT FLOW =====
When user wants to CANCEL an appointment:
STEP 1: Show today's schedule with appointment IDs:
SHOW_OPTIONS:{{"type":"cancel_select","question":"Which appointment to cancel?","options":[{{"id":<appointment_id>,"label":"<time> - <patient>","subtitle":"<treatment>"}},...]}}
STEP 2: After user selects → ask confirm:
SHOW_OPTIONS:{{"type":"confirm_cancel","question":"Cancel this appointment?","options":[{{"id":"yes","label":"✅ Yes, Cancel"}},{{"id":"no","label":"❌ No, Keep it"}}]}}
STEP 3: If YES →
ACTION:CANCEL_APPOINTMENT:{{"appointment_id":<id>}}

===== RULES =====
- ALWAYS show the list BEFORE asking the question — never ask without showing options
- Use db_id (not patient_id like Aura49) for BOOK_APPOINTMENT patient_id field
- price_plan_id: use the first price plan id from the selected treatment
- Only ONE action per response, on its own line
- After booking/cancelling confirm to the user with a friendly message
- For questions NOT about booking/cancelling, just answer from the clinic data
"""


def _call_api(method, endpoint, token, body=None, params=None):
    base_url = "https://auro-backend-api.onrender.com/api"
    headers  = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url      = f"{base_url}{endpoint}"
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, params=params, timeout=15)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, json=body, timeout=15)
        elif method == 'PATCH':
            resp = requests.patch(url, headers=headers, json=body, timeout=15)
        return resp.status_code, resp.json()
    except Exception as e:
        return 500, {'error': str(e)}


def _execute_action(action_line, token):
    try:
        if action_line.startswith("ACTION:GET_SLOTS:"):
            params     = json.loads(action_line.split("ACTION:GET_SLOTS:")[1])
            staff_id   = params.get('staff_id')
            service_id = params.get('service_id')
            month      = params.get('month')  # YYYY-MM

            try:
                import datetime, calendar
                from appointments.models import Appointment
                from users.models import StaffWorkingHours, StaffBreakTime, StaffLeave
                from treatments.models import Treatment

                year, mon    = map(int, month.split('-'))
                days_in_month = calendar.monthrange(year, mon)[1]
                today_date   = datetime.date.today()

                try:
                    duration = Treatment.objects.get(id=service_id).duration
                except:
                    duration = 60

                working_hours = {wh.day: wh for wh in StaffWorkingHours.objects.filter(staff_id=staff_id)}
                DAY_MAP = {0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'}

                leaves = StaffLeave.objects.filter(staff_id=staff_id)
                leave_dates = set()
                for leave in leaves:
                    d = leave.from_date
                    while d <= leave.to_date:
                        leave_dates.add(d)
                        d += datetime.timedelta(days=1)

                breaks = list(StaffBreakTime.objects.filter(staff_id=staff_id))

                month_start = datetime.date(year, mon, 1)
                month_end   = datetime.date(year, mon, days_in_month)
                bookings = Appointment.objects.filter(
                    staff_id=staff_id,
                    date_time__date__gte=month_start,
                    date_time__date__lte=month_end,
                    status__in=['upcoming', 'in_session']
                ).values('date_time', 'duration')

                booked_slots = {}
                for b in bookings:
                    d = b['date_time'].date()
                    if d not in booked_slots:
                        booked_slots[d] = []
                    booked_slots[d].append((b['date_time'].time(), b['duration']))

                available_dates = {}
                for day_num in range(1, days_in_month + 1):
                    date     = datetime.date(year, mon, day_num)
                    if date < today_date:
                        continue
                    if date in leave_dates:
                        continue
                    day_name = DAY_MAP[date.weekday()]
                    if day_name not in working_hours:
                        continue

                    wh    = working_hours[day_name]
                    start = datetime.datetime.combine(date, wh.start_time)
                    end   = datetime.datetime.combine(date, wh.end_time)
                    slots = []
                    cur   = start

                    while cur + datetime.timedelta(minutes=duration) <= end:
                        slot_time = cur.time()
                        slot_end  = (cur + datetime.timedelta(minutes=duration)).time()
                        blocked   = False

                        for br in breaks:
                            if slot_time < br.end_time and slot_end > br.start_time:
                                blocked = True
                                break

                        if not blocked and date in booked_slots:
                            for bt, bd in booked_slots[date]:
                                bt_end = (datetime.datetime.combine(date, bt) + datetime.timedelta(minutes=bd)).time()
                                if slot_time < bt_end and slot_end > bt:
                                    blocked = True
                                    break

                        if not blocked:
                            slots.append(cur.strftime('%H:%M'))
                        cur += datetime.timedelta(minutes=30)

                    if slots:
                        available_dates[str(date)] = slots

                return {'action': 'GET_SLOTS', 'status': 200, 'data': available_dates}

            except Exception as e:
                return {'action': 'GET_SLOTS', 'status': 500, 'data': {'error': str(e)}}

        elif action_line.startswith("ACTION:BOOK_APPOINTMENT:"):
            try:
                # Clean up common AI JSON mistakes
                raw = action_line.split("ACTION:BOOK_APPOINTMENT:")[1]
                # Fix single quotes, trailing commas etc
                raw = raw.strip()
                body = json.loads(raw)
            except Exception:
                # Try to extract values using regex
                import re
                raw  = action_line.split("ACTION:BOOK_APPOINTMENT:")[1]
                body = {}
                for key in ['patient_id','staff_id','treatment_id','room_id','price_plan_id']:
                    m = re.search(rf'"{key}"\s*:\s*(\d+)', raw)
                    if m:
                        body[key] = int(m.group(1))
                for key in ['date','time']:
                    m = re.search(rf'"{key}"\s*:\s*"([^"]+)"', raw)
                    if m:
                        body[key] = m.group(1)

            if not body or 'patient_id' not in body:
                return {'action': 'BOOK_APPOINTMENT', 'success': False,
                        'message': '❌ Could not parse booking details. Please try again.'}

            status, data = _call_api('POST', '/appointments/', token, body=body)
            if status == 201:
                return {'action': 'BOOK_APPOINTMENT', 'success': True, 'data': data,
                        'message': f"✅ Appointment booked! ID: {data.get('id')}"}
            else:
                return {'action': 'BOOK_APPOINTMENT', 'success': False, 'data': data,
                        'message': f"❌ Booking failed: {data}"}

        elif action_line.startswith("ACTION:CANCEL_APPOINTMENT:"):
            body   = json.loads(action_line.split("ACTION:CANCEL_APPOINTMENT:")[1])
            appt_id = body.get('appointment_id')
            status, data = _call_api('PATCH', f'/appointments/{appt_id}/status/', token, body={'status': 'cancelled'})
            if status == 200:
                return {'action': 'CANCEL_APPOINTMENT', 'success': True,
                        'message': f"✅ Appointment #{appt_id} has been cancelled."}
            else:
                return {'action': 'CANCEL_APPOINTMENT', 'success': False, 'data': data,
                        'message': f"❌ Cancel failed: {data}"}

    except Exception as e:
        return {'action': 'ERROR', 'message': str(e)}

    return None


class AIChatView(APIView):
    """
    POST /api/ai/chat/
    Conversational AI that can book and cancel appointments.

    Body:
    {
        "message": "Book an appointment",
        "conversation_history": []
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from users.models import User as UserModel

        message = request.data.get('message', '').strip()
        history = request.data.get('conversation_history', [])
        token   = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '').strip()

        if not message:
            return Response({'error': 'message is required.'}, status=400)

        try:
            user = UserModel.objects.get(pk=request.user.pk)
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        try:
            context = _get_clinic_context(user)
        except Exception as e:
            context = {'role': getattr(user, 'role', ''), 'name': user.username,
                       'today': str(timezone.localdate()), 'patients': [], 'therapists': [],
                       'treatments': [], 'rooms': []}

        system_prompt = _build_system_prompt(user, context)

        # Build Groq messages (OpenAI format)
        groq_messages = [{'role': 'system', 'content': system_prompt}]
        for h in history:
            if h.get('role') == 'user':
                groq_messages.append({'role': 'user', 'content': h['content']})
            elif h.get('role') == 'assistant':
                groq_messages.append({'role': 'assistant', 'content': h['content']})
        groq_messages.append({'role': 'user', 'content': message})

        def _call_groq(messages, api_key):
            resp = requests.post(
                GROQ_API_URL,
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={'model': GROQ_MODEL, 'messages': messages, 'max_tokens': 1024, 'temperature': 0.3},
                timeout=30,
            )
            return resp.status_code, resp

        try:
            api_key = os.environ.get('GROQ_API_KEY', '')
            if not api_key:
                return Response({'error': 'AI service not configured.'}, status=503)

            status_code, response = _call_groq(groq_messages, api_key)

            if status_code != 200:
                return Response({'error': 'AI service error.', 'detail': response.text}, status=503)

            data  = response.json()
            reply = data['choices'][0]['message']['content']

            # Detect action or options in reply
            action_result  = None
            options_result = None
            action_line    = None
            clean_reply    = reply

            for line in reply.split('\n'):
                line_stripped = line.strip()
                if line_stripped.startswith('ACTION:'):
                    action_line = line_stripped
                    clean_reply = reply.replace(line, '').strip()
                    break
                elif line_stripped.startswith('SHOW_OPTIONS:'):
                    try:
                        options_json   = line_stripped.split('SHOW_OPTIONS:')[1]
                        options_result = json.loads(options_json)
                        clean_reply    = reply.replace(line, '').strip()
                    except Exception:
                        pass
                    break

            if action_line and token:
                action_result = _execute_action(action_line, token)

                # If GET_SLOTS — process slots and show available dates
                if action_result and action_result.get('action') == 'GET_SLOTS':
                    slot_data = action_result.get('data', {})
                    if action_result.get('status') != 200:
                        follow_up = "The slot lookup failed. Tell the user there was an error getting available slots and ask them to try again."
                    elif not slot_data:
                        follow_up = "There are no available slots this month for this therapist. Tell the user and suggest picking a different therapist or month."
                    else:
                        follow_up = f"""Available dates and slots:
{json.dumps(slot_data, indent=2)}

The data is a dictionary where key=date (YYYY-MM-DD) and value=list of available times (HH:MM).
Show the available DATES as clickable options:
SHOW_OPTIONS:{{"type":"date","question":"Which date would you like?","options":[{{"id":"YYYY-MM-DD","label":"Day, DD Mon YYYY","subtitle":"X slots available"}},...all available dates...]}}
Format the label nicely e.g. "Mon, 20 May 2026". Count the slots for subtitle."""

                    groq_messages.append({'role': 'assistant', 'content': clean_reply})
                    groq_messages.append({'role': 'user', 'content': follow_up})

                    status_code2, response2 = _call_groq(groq_messages, api_key)
                    if status_code2 == 200:
                        data2       = response2.json()
                        clean_reply = data2['choices'][0]['message']['content']
                        # Parse options from second response
                        for line in clean_reply.split('\n'):
                            if line.strip().startswith('SHOW_OPTIONS:'):
                                try:
                                    options_result = json.loads(line.strip().split('SHOW_OPTIONS:')[1])
                                    clean_reply    = clean_reply.replace(line, '').strip()
                                except Exception:
                                    pass
                                break

                elif action_result and action_result.get('action') in ['BOOK_APPOINTMENT', 'CANCEL_APPOINTMENT']:
                    clean_reply = f"{clean_reply}\n\n{action_result.get('message', '')}".strip()

            return Response({
                'reply':         clean_reply,
                'role':          context.get('role'),
                'action_result': action_result,
                'options':       options_result,
                'context': {
                    'name':  context.get('name'),
                    'today': context.get('today'),
                },
            })

        except requests.Timeout:
            return Response({'error': 'AI response timed out.'}, status=504)
        except Exception as e:
            return Response({'error': f'AI service error: {str(e)}'}, status=503)