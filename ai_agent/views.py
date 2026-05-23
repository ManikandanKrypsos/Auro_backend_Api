from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.utils.timezone import localtime
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
        {
            'db_id':             p.id,
            'patient_id':        p.patient_id,
            'name':              p.name,
            'phone':             p.phone,
            'email':             p.email or '',
            'gender':            p.gender or '',
            'dob':               str(p.dob) if p.dob else '',
            'blood_type':        p.blood_type or '',
            'allergies':         p.allergies or 'None',
            'skin_type':         p.skin_type or '',
            'contraindications': p.contraindications or '',
            'notes':             p.notes or '',
            'category':          p.category or '',
        }
        for p in Patient.objects.all().order_by('name')[:50]
    ]
    context['therapists'] = [
        {'id': s.id, 'name': s.username or s.email.split('@')[0], 'specialist_area': s.specialist_area, 'phone': s.phone, 'email': s.email}
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
            {'time': localtime(a.date_time).strftime('%H:%M') if a.date_time else None, 'patient': a.patient.name if a.patient else None,
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
            {'appointment_id': a.id, 'time': localtime(a.date_time).strftime('%H:%M') if a.date_time else None,
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
        context['revenue_this_month']   = float(month_appts.filter(payment_status='paid').aggregate(t=Sum('payment_amount'))['t'] or 0)
        context['todays_schedule'] = [
            {'appointment_id': a.id, 'time': localtime(a.date_time).strftime('%H:%M') if a.date_time else None,
             'patient': a.patient.name if a.patient else None, 'treatment': a.treatment.name if a.treatment else None,
             'therapist': a.staff.username if a.staff else None, 'status': a.status}
            for a in todays_appts.select_related('patient', 'treatment', 'staff').order_by('date_time')
        ]

    return context


def _build_system_prompt(user, context):
    role = context.get('role', '')
    name = context.get('name', '')

    # Build readable lists for AI to use
    patients_list   = '\n'.join([
        f"{i+1}. {p['name']} | Phone: {p['phone']} | Skin: {p.get('skin_type','N/A')} | Allergies: {p.get('allergies','None')} | Gender: {p.get('gender','N/A')}"
        for i, p in enumerate(context.get('patients', []))
    ])
    therapists_list = '\n'.join([f"{i+1}. {t['name']} - {t.get('specialist_area','')}" for i, t in enumerate(context.get('therapists', []))])
    treatments_list = '\n'.join([f"{i+1}. {t['name']} ({t['duration']} min)" for i, t in enumerate(context.get('treatments', []))])
    rooms_list      = '\n'.join([f"{i+1}. {r['name']}" for i, r in enumerate(context.get('rooms', []))])

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

===== PATIENT & STAFF INFORMATION =====
You have FULL access to all patient and staff details. Answer SPECIFICALLY what is asked.
- If asked "Vini's allergies" → show ONLY allergies
- If asked "Vini's skin type" → show ONLY skin type  
- If asked "Vini's phone" → show ONLY phone number
- If asked "tell me about Vini" or "Vini's details" → show everything
- Also suggest relevant treatments based on patient's skin type and allergies when asked
- Staff phone, email, specialist area — share when asked
- NEVER say "not available for public display" — all data is internal clinic data for staff use

===== TREATMENT RECOMMENDATION =====
When user asks "suggest a treatment", "what treatment for X", "recommend treatment" or describes a skin/body concern, suggest treatments from the AVAILABLE TREATMENTS list based on their description.

Examples:
- "patient has dry skin" → suggest hydrating/moisturizing treatments
- "patient wants anti-aging" → suggest age control treatments
- "patient has acne" → suggest deep cleanse treatments
- "patient wants body treatment" → suggest body category treatments

Format your recommendation like:
"Based on [concern], I recommend:
1. [Treatment Name] — [reason why it fits] ([duration] min)
2. [Treatment Name] — [reason why it fits] ([duration] min)

Would you like to book one of these?"

If user says yes → start the booking flow with the recommended treatment pre-selected.
When user wants to BOOK an appointment, follow this conversational flow like a WhatsApp chat.
Check conversation history — if patient/treatment/therapist/room/date already confirmed, skip those steps.

STEP 1 — PATIENT:
When user says "book appointment" → immediately show this EXACT patient list:
"Here are the available patients:
{patients_list}

Type a number to select, or type a name to search."
When user replies with a number → confirm and immediately show treatments list (STEP 2).

===== CREATE PATIENT FLOW =====
When user says "create patient", "add patient", "new patient":
Ask questions ONE BY ONE:
1. "What is the patient's full name?"
2. "What is their phone number?"
3. "What is their email? (or type 'skip')"
4. "What is their gender? (Male/Female/Other)"
5. "What is their date of birth? (YYYY-MM-DD or type 'skip')"
6. "What is their city? (or type 'skip')"
7. "What is their country? (or type 'skip')"
8. "What is their blood group? (A+/A-/B+/B-/AB+/AB-/O+/O- or type 'skip')"
9. "Any allergies? (or type 'none')"
10. "What is their skin type? (Normal/Dry/Oily/Combination/Sensitive or type 'skip')"

After collecting all → show summary and ask confirm:
"Patient Summary:
👤 Name: [name]
📞 Phone: [phone]
📧 Email: [email]
⚧ Gender: [gender]
🎂 DOB: [dob]
🏙 City: [city]
🌍 Country: [country]
🩸 Blood Group: [blood_group]
⚠️ Allergies: [allergies]
💆 Skin Type: [skin_type]

Confirm? Reply YES to create."

If YES → respond with:
ACTION:CREATE_PATIENT:{{"name":"<name>","phone":"<phone>","email":"<email>","gender":"<gender>","dob":"<dob>","city":"<city>","country":"<country>","blood_type":"<blood_group>","allergies":"<allergies>","skin_type":"<skin_type>"}}

STEP 2 — TREATMENT:
Immediately after patient confirmed → show this EXACT treatments list:
"[Name] selected ✅

Which treatment?
{treatments_list}

Reply with a number:"

STEP 3 — THERAPIST:
Immediately after treatment confirmed → show this EXACT therapists list:
"[Treatment] selected ✅

Which therapist?
{therapists_list}

Reply with a number:"

STEP 4 — ROOM:
Immediately after therapist confirmed → show this EXACT rooms list:
"[Therapist] selected ✅

Which room?
{rooms_list}

Reply with a number:"
NEVER say "Fetching available dates" without first getting room selection.
NEVER trigger ACTION:GET_SLOTS without room_id.
Wait for user to pick a room number before proceeding.
When user picks a room number → look up the room id from AVAILABLE ROOMS list above → confirm: "[Room] selected ✅" then on the NEXT LINE write ONLY:
ACTION:GET_SLOTS:{{"staff_id":<actual_staff_id>,"service_id":<actual_treatment_id>,"month":"CURRENT_MONTH","room_id":<actual_room_id>}}
Replace CURRENT_MONTH with today's year-month e.g. 2026-05
Replace all IDs with actual numeric IDs from the selected items — not placeholder text.

STEP 5 — DATE (after slots data returned):
Show available dates as numbered list:
"Available dates for [Therapist]:
1. Mon, 19 May 2026 (5 slots)
2. Tue, 20 May 2026 (3 slots)
3. Wed, 21 May 2026 (4 slots)

Reply with a number:"
If no dates: "No available dates this month for [Therapist]. Try a different therapist?"

STEP 6 — TIME SLOT:
Show available times for selected date as numbered list:
"Available slots on [Date]:
1. 09:00 AM
2. 10:30 AM
3. 02:00 PM
4. 03:30 PM

Reply with a number:"
If no slots: "No slots available on this date. Please pick another date."

STEP 7 — CONFIRM:
Show full summary and ask:
"Here's the booking summary:
👤 Patient: [Name]
💆 Treatment: [Treatment]
👩‍⚕️ Therapist: [Therapist]
🚪 Room: [Room]
📅 Date: [Date]
⏰ Time: [Time]

Confirm booking? Reply YES to confirm or NO to cancel."

STEP 8 — BOOK:
If user says YES/yes/confirm/ok:
ACTION:BOOK_APPOINTMENT:{{"patient_id":<db_id>,"staff_id":<id>,"treatment_id":<id>,"room_id":<id>,"price_plan_id":<id>,"date":"YYYY-MM-DD","time":"HH:MM"}}
Then say: "✅ Appointment booked successfully!"

===== CANCEL APPOINTMENT FLOW =====
When user wants to CANCEL:
Show today's schedule as numbered list:
"Today's appointments:
1. 10:30 AM - Emma Garcia (AURA AGE CONTROL) [ID: 45]
2. 02:00 PM - John Smith (Hydra Glow) [ID: 46]

Which one to cancel? Reply with a number:"
After selection: "Cancel appointment for [Patient] at [Time]? Reply YES or NO"
If YES:
ACTION:CANCEL_APPOINTMENT:{{"appointment_id":<id>}}
Then say: "✅ Appointment cancelled."

===== IMPORTANT RULES =====
- Always show numbered lists — never ask without showing options
- When user types a name for search, do fuzzy match from AVAILABLE PATIENTS list
- When user replies with a NUMBER ONLY like "1", "2", "3" → select from the last shown list
- When user asks "give me [name] number" or "[name] phone" or "[name] contact" → show that patient's PHONE NUMBER from the patients list, do NOT select them for booking
- When user says "select [name]" or "[name]" or picks a number → select for booking
- Keep track of all selections in conversation — never ask again what was already confirmed
- db_id is the numeric id (not Aura49 format) — use it for BOOK_APPOINTMENT patient_id
- price_plan_id: use the first price plan id from the selected treatment's price_plans list
- Only ONE action per response on its own line
- Be friendly and concise — like a WhatsApp assistant
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
                # Use local timezone for today
                from django.utils.timezone import localdate, localtime as ltime
                today_date   = localdate()
                now_local    = ltime(timezone.now())

                try:
                    duration = Treatment.objects.get(id=service_id).duration
                except:
                    duration = 60

                working_hours = {wh.day: wh for wh in StaffWorkingHours.objects.filter(staff_id=staff_id)}

                # If no working hours set, use full day as fallback
                if not working_hours:
                    from users.models import StaffWorkingHours as SWH
                    import datetime as dt2
                    for day in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
                        class FakeWH:
                            start_time = dt2.time(9, 0)
                            end_time   = dt2.time(18, 0)
                        working_hours[day] = FakeWH()
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
                    appt_dt = b['date_time']
                    # Handle timezone aware datetimes
                    if hasattr(appt_dt, 'tzinfo') and appt_dt.tzinfo:
                        import pytz
                        appt_dt = appt_dt.astimezone(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None)
                    d = appt_dt.date()
                    if d not in booked_slots:
                        booked_slots[d] = []
                    booked_slots[d].append((appt_dt.time(), b['duration']))

                available_dates = {}
                for day_num in range(1, days_in_month + 1):
                    date     = datetime.date(year, mon, day_num)
                    if date < today_date:  # skip past dates
                        continue
                    if date == today_date:  # for today, only show future slots
                        pass
                    if date in leave_dates:
                        continue
                    day_name = DAY_MAP[date.weekday()]
                    if day_name not in working_hours:
                        continue

                    wh    = working_hours[day_name]
                    start = datetime.datetime.combine(date, wh.start_time)
                    end   = datetime.datetime.combine(date, wh.end_time)

                    # For today, start from current time (rounded up to next 30 min)
                    if date == today_date:
                        from django.utils.timezone import localtime as ltime2
                        from django.utils import timezone as dj_tz2
                        now_time = ltime2(dj_tz2.now()).replace(tzinfo=None)
                        # Round up to next 30 minute slot
                        minutes  = now_time.minute
                        if minutes == 0:
                            rounded = now_time.replace(second=0, microsecond=0)
                        elif minutes <= 30:
                            rounded = now_time.replace(minute=30, second=0, microsecond=0)
                        else:
                            rounded = (now_time + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                        if rounded > start:
                            start = rounded
                    slots = []
                    cur   = start

                    while cur + datetime.timedelta(minutes=duration) <= end:
                        slot_time = cur.time()
                        slot_end  = (cur + datetime.timedelta(minutes=duration)).time()

                        # Check slot doesn't exceed clinic closing time
                        try:
                            from clinic.models import ClinicHours
                            day_name_clinic = date.strftime('%a')
                            ch = ClinicHours.objects.filter(day=day_name_clinic, is_open=True).first()
                            if ch and ch.close_time and slot_end > ch.close_time:
                                cur += datetime.timedelta(minutes=30)
                                continue
                        except Exception:
                            pass

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
                import re, datetime
                from appointments.models import Appointment
                from patients.models import Patient
                from users.models import User as StaffUser
                from treatments.models import Treatment, PricePlan
                from rooms.models import Room

                raw = action_line.split("ACTION:BOOK_APPOINTMENT:")[1].strip()
                try:
                    body = json.loads(raw)
                except Exception:
                    body = {}
                    for key in ['patient_id','staff_id','treatment_id','room_id','price_plan_id']:
                        m = re.search(rf'"{key}"\s*:\s*(\d+)', raw)
                        if m:
                            body[key] = int(m.group(1))
                    for key in ['date','time']:
                        m = re.search(rf'"{key}"\s*:\s*"([^"]+)"', raw)
                        if m:
                            body[key] = m.group(1)

                patient   = Patient.objects.get(id=body['patient_id'])
                staff     = StaffUser.objects.get(id=body['staff_id'])
                treatment = Treatment.objects.get(id=body['treatment_id'])
                room      = Room.objects.get(id=body['room_id'])
                plan      = PricePlan.objects.get(id=body['price_plan_id'])

                date_str  = body['date']
                time_str  = body['time'].split('-')[0].strip()
                dt        = datetime.datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                from django.utils import timezone as tz
                dt_aware  = tz.make_aware(dt)

                appt = Appointment.objects.create(
                    patient=patient,
                    staff=staff,
                    treatment=treatment,
                    room_fk=room,
                    price_plan=plan,
                    date_time=dt_aware,
                    duration=treatment.duration,
                    session_number=1,
                    total_sessions=plan.sessions,
                    status='upcoming',
                    payment_status='pending',
                    consent_status='pending',
                    payment_type='cash',
                )
                return {
                    'action':  'BOOK_APPOINTMENT',
                    'success': True,
                    'data':    {'id': appt.id},
                    'message': f"✅ Appointment booked! ID: {appt.id} — {patient.name} on {date_str} at {time_str} with {staff.username}."
                }
            except Exception as e:
                return {
                    'action':  'BOOK_APPOINTMENT',
                    'success': False,
                    'message': f"❌ Booking failed: {str(e)}"
                }

        elif action_line.startswith("ACTION:CANCEL_APPOINTMENT:"):
            try:
                import re
                from appointments.models import Appointment
                raw = action_line.split("ACTION:CANCEL_APPOINTMENT:")[1]
                try:
                    body    = json.loads(raw)
                    appt_id = body.get('appointment_id')
                except Exception:
                    m       = re.search(r'(\d+)', raw)
                    appt_id = int(m.group(1)) if m else None

                if not appt_id:
                    return {'action': 'CANCEL_APPOINTMENT', 'success': False,
                            'message': '❌ Could not find appointment ID.'}

                appt = Appointment.objects.get(id=appt_id)
                appt.status = 'cancelled'
                appt.save()
                return {'action': 'CANCEL_APPOINTMENT', 'success': True,
                        'message': f"✅ Appointment #{appt_id} has been cancelled."}
            except Exception as e:
                return {'action': 'CANCEL_APPOINTMENT', 'success': False,
                        'message': f"❌ Cancel failed: {str(e)}"}

        elif action_line.startswith("ACTION:CREATE_PATIENT:"):
            try:
                import re
                from patients.models import Patient

                raw  = action_line.split("ACTION:CREATE_PATIENT:")[1].strip()
                try:
                    body = json.loads(raw)
                except Exception:
                    body = {}
                    for key in ['name','phone','email','gender','dob','allergies','skin_type']:
                        m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', raw)
                        if m:
                            body[key] = m.group(1)

                if not body.get('name') or not body.get('phone'):
                    return {'action': 'CREATE_PATIENT', 'success': False,
                            'message': '❌ Name and phone are required.'}

                # Auto generate patient_id
                last = Patient.objects.order_by('-id').first()
                next_id = (last.id + 1) if last else 1
                patient_id = f"Aura{next_id}"

                patient = Patient.objects.create(
                    patient_id  = patient_id,
                    name        = body.get('name', ''),
                    phone       = body.get('phone', ''),
                    email       = body.get('email', '') if body.get('email') != 'skip' else '',
                    gender      = body.get('gender', ''),
                    dob         = body.get('dob') if body.get('dob') and body.get('dob') != 'skip' else None,
                    city        = body.get('city', '') if body.get('city') != 'skip' else '',
                    country     = body.get('country', '') if body.get('country') != 'skip' else '',
                    blood_type  = body.get('blood_type', '') if body.get('blood_type') != 'skip' else '',
                    allergies   = body.get('allergies', '') if body.get('allergies') != 'none' else '',
                    skin_type   = body.get('skin_type', '') if body.get('skin_type') != 'skip' else '',
                    category    = 'New',
                )
                return {
                    'action':  'CREATE_PATIENT',
                    'success': True,
                    'message': f"✅ Patient created! ID: {patient.patient_id} — {patient.name}",
                    'data':    {'id': patient.id, 'patient_id': patient.patient_id, 'name': patient.name}
                }
            except Exception as e:
                return {'action': 'CREATE_PATIENT', 'success': False,
                        'message': f"❌ Failed to create patient: {str(e)}"}

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
            for attempt in range(4):  # retry up to 4 times
                try:
                    resp = requests.post(
                        GROQ_API_URL,
                        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                        json={'model': GROQ_MODEL, 'messages': messages, 'max_tokens': 1024, 'temperature': 0.3},
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        return resp.status_code, resp
                    elif resp.status_code == 429:  # rate limit - wait and retry
                        import time
                        time.sleep(2 * (attempt + 1))
                        continue
                    else:
                        return resp.status_code, resp
                except requests.Timeout:
                    if attempt == 3:
                        raise
                    import time
                    time.sleep(1)
            return 503, None

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

            # If reply is empty after parsing, use options question as reply
            if not clean_reply and options_result:
                clean_reply = options_result.get('question', 'Please choose an option:')
            elif not clean_reply and action_line:
                if action_result and action_result.get('success'):
                    clean_reply = action_result.get('message', '✅ Done!')
                else:
                    clean_reply = action_result.get('message', '❌ Something went wrong.') if action_result else 'Processing...'

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
                        if not clean_reply and options_result:
                            clean_reply = options_result.get('question', 'Please choose a date:')

                elif action_result and action_result.get('action') in ['BOOK_APPOINTMENT', 'CANCEL_APPOINTMENT', 'CREATE_PATIENT']:
                    msg = action_result.get('message', '')
                    if action_result.get('action') == 'CREATE_PATIENT' and action_result.get('success'):
                        clean_reply = f"✅ Patient created successfully!\n{msg}"
                    else:
                        clean_reply = f"{clean_reply}\n\n{msg}".strip()

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