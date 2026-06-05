from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.utils.timezone import localtime
import json
import requests
import os


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"


def _get_clinic_context(user):
    from appointments.models import Appointment
    from patients.models import Patient
    from users.models import User as UserModel
    from treatments.models import Treatment
    from rooms.models import Room
    from inventory.models import InventoryItem

    today = timezone.localdate()
    now   = timezone.now()
    role  = getattr(user, 'role', '') or ''
    name  = user.username or user.email.split('@')[0]

    context = {'role': role, 'name': name, 'today': str(today)}

    # All roles get full access to all data
    context['patients'] = [
        {
            'db_id':      p.id,
            'patient_id': p.patient_id,
            'name':       p.name,
            'phone':      p.phone,
            'email':      p.email or '',
            'gender':     p.gender or '',
            'dob':        str(p.dob) if p.dob else '',
            'blood_type': p.blood_type or '',
            'allergies':  p.allergies or 'None',
            'skin_type':  p.skin_type or '',
            'city':       p.city or '',
            'country':    p.country or '',
            'contraindications': p.contraindications or '',
            'notes':      p.notes or '',
            'category':   p.category or '',
        }
        for p in Patient.objects.all().order_by('name')[:50]
    ]
    context['therapists'] = [
        {
            'id':              s.id,
            'name':            s.username or s.email.split('@')[0],
            'specialist_area': s.specialist_area,
            'phone':           s.phone,
            'email':           s.email,
        }
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

    # Schedule and stats — all roles get all data
    from django.db.models import Sum
    import datetime as dt
    local_today    = timezone.localdate()
    start_of_month = dt.date(local_today.year, local_today.month, 1)
    todays_appts   = Appointment.objects.filter(date_time__date=local_today)
    month_appts    = Appointment.objects.filter(date_time__date__gte=start_of_month)

    # If therapist — show their own schedule too
    if role == 'therapist':
        my_appts = Appointment.objects.filter(staff=user, date_time__date=today).select_related('patient', 'treatment')
        context['my_schedule_today'] = [
            {
                'time':           localtime(a.date_time).strftime('%H:%M') if a.date_time else None,
                'patient':        a.patient.name if a.patient else None,
                'treatment':      a.treatment.name if a.treatment else None,
                'status':         a.status,
                'appointment_id': a.id,
            }
            for a in my_appts.order_by('date_time')
        ]
        context['my_total_today']     = my_appts.count()
        context['my_completed_today'] = my_appts.filter(status='completed').count()

    context['todays_appointments']  = todays_appts.count()
    context['monthly_appointments'] = month_appts.count()
    context['revenue_today']        = float(todays_appts.filter(payment_status='paid').aggregate(t=Sum('payment_amount'))['t'] or 0)
    context['revenue_this_month']   = float(month_appts.filter(payment_status='paid').aggregate(t=Sum('payment_amount'))['t'] or 0)
    context['checked_in_today']     = todays_appts.filter(patient_arrived=True).count()
    context['cancelled_today']      = todays_appts.filter(status='cancelled').count()
    context['in_session_today']     = todays_appts.filter(status='in_session').count()
    context['todays_schedule'] = [
        {
            'appointment_id': a.id,
            'time':           localtime(a.date_time).strftime('%H:%M') if a.date_time else None,
            'patient':        a.patient.name if a.patient else None,
            'treatment':      a.treatment.name if a.treatment else None,
            'therapist':      a.staff.username if a.staff else None,
            'status':         a.status,
        }
        for a in todays_appts.select_related('patient', 'treatment', 'staff').order_by('date_time')
    ]

    # Inventory stock levels
    context['inventory'] = [
        {
            'id':            item.id,
            'name':          item.name,
            'current_stock': item.current_stock,
            'minimum_stock': item.minimum_stock_alert,
            'unit':          item.unit,
            'category':      item.category,
            'status':        'out_of_stock' if item.current_stock == 0 else 'low_stock' if item.current_stock <= item.minimum_stock_alert else 'in_stock',
        }
        for item in InventoryItem.objects.all().order_by('name')
    ]

    # Today's pending payments
    context['pending_payments_today'] = [
        {
            'appointment_id': a.id,
            'patient':        a.patient.name if a.patient else '',
            'treatment':      a.treatment.name if a.treatment else '',
            'amount':         f"€{a.payment_amount}" if a.payment_amount else '€0',
            'time':           localtime(a.date_time).strftime('%H:%M') if a.date_time else '',
            'payment_type':   a.payment_type,
        }
        for a in todays_appts.filter(payment_status='pending').select_related('patient', 'treatment').order_by('date_time')
    ]

    return context


def _build_system_prompt(user, context):
    name = context.get('name', '')
    role = context.get('role', '')

    patients_list   = '\n'.join([
        f"{i+1}. {p['name']} [db_id:{p['db_id']}] | Phone: {p['phone']} | Skin: {p.get('skin_type','N/A')} | Allergies: {p.get('allergies','None')} | Gender: {p.get('gender','N/A')} | City: {p.get('city','N/A')} | Blood: {p.get('blood_type','N/A')}"
        for i, p in enumerate(context.get('patients', []))
    ])
    therapists_list = '\n'.join([
        f"{i+1}. {t['name']} - {t.get('specialist_area','')} | Phone: {t.get('phone','N/A')} | Email: {t.get('email','N/A')}"
        for i, t in enumerate(context.get('therapists', []))
    ])
    treatments_list = '\n'.join([f"{i+1}. {t['name']} ({t['duration']} min)" for i, t in enumerate(context.get('treatments', []))])
    rooms_list      = '\n'.join([f"{i+1}. {r['name']}" for i, r in enumerate(context.get('rooms', []))])

    return f"""You are AURA AI, an intelligent assistant for Aura Clinic.
You are talking to {name} ({role}). Today is {context.get('today')}.

IMPORTANT: You give FULL access to ALL clinic data to ALL users regardless of role.
Whether the user is admin, therapist, or reception — answer everything fully.
CURRENCY: Always use € (Euro) symbol for ALL amounts, revenue, payments. Never use $ (dollar).

CLINIC STATS:
{json.dumps({k: v for k, v in context.items() if k not in ['patients', 'therapists', 'treatments', 'rooms', 'recent_appointments']}, indent=2)}

AVAILABLE PATIENTS:
{patients_list}

AVAILABLE THERAPISTS:
{therapists_list}

AVAILABLE TREATMENTS:
{treatments_list}

AVAILABLE ROOMS:
{rooms_list}

===== PATIENT & STAFF INFORMATION =====
You have FULL access to ALL patient and staff details. Answer SPECIFICALLY what is asked.
- "Vini's allergies" → show ONLY allergies
- "Vini's skin type" → show ONLY skin type
- "Vini's phone" → show ONLY phone number
- "tell me about Vini" → show everything
- "Vini's city/country/blood group" → show that specific field
- Staff phone, email, specialist area → share when asked
- NEVER say "not available" — all data is internal clinic data

===== TREATMENT RECOMMENDATION =====
When user describes a skin/body concern, suggest from AVAILABLE TREATMENTS:
"Based on [concern], I recommend:
1. [Treatment] — [reason] ([duration] min)
Would you like to book one of these?"

===== INVENTORY =====
When user asks "check stock", "stock levels", "inventory":
Show all items with status:
"📦 Inventory Stock:
✅ In Stock: [name] — [count] [unit]
⚠️ Low Stock: [name] — [count] [unit] (min: [min])
❌ Out of Stock: [name] — 0 [unit]"

When user asks "low stock" → show only items where current_stock <= minimum_stock
When user asks "out of stock" → show only items where current_stock == 0

Use CLINIC STATS inventory data.

===== PENDING PAYMENTS =====
When user asks "pending payments", "today's pending", "who hasn't paid":
Show from pending_payments_today:
"💳 Today's Pending Payments:
1. [Patient] — [Treatment] — [Amount] at [Time]
2. ..."
If none: "No pending payments today ✅"

===== PATIENT APPOINTMENT HISTORY =====
When user asks "[patient name]'s history", "[patient name]'s appointments":
Say: "For detailed appointment history, please check the patient profile in the app."
STEP 1 — PATIENT: Show exact list:
"Here are the available patients:
{patients_list}
Type a number to select."

STEP 2 — TREATMENT (immediately after patient selected):
"[Name] selected ✅
Which treatment?
{treatments_list}
Reply with a number:"

STEP 3 — THERAPIST (immediately after treatment selected):
"[Treatment] selected ✅
Which therapist?
{therapists_list}
Reply with a number:"

STEP 4 — ROOM (immediately after therapist selected):
"[Therapist] selected ✅
Which room?
{rooms_list}
Reply with a number:"
NEVER fetch slots without room. When room picked, on the NEXT LINE write ONLY:
ACTION:GET_SLOTS:{{"staff_id":<id>,"service_id":<id>,"month":"{context.get('today','2026-05-23')[:7]}","room_id":<id>}}

STEP 5 — DATE: Show available dates as numbered list.
STEP 6 — TIME: Show available times for selected date.
STEP 7 — CONFIRM: Show full summary → ask YES/NO.
STEP 8 — BOOK: If YES:
ACTION:BOOK_APPOINTMENT:{{"patient_id":<db_id>,"staff_id":<id>,"treatment_id":<id>,"room_id":<id>,"price_plan_id":<id>,"date":"YYYY-MM-DD","time":"HH:MM"}}

===== CANCEL APPOINTMENT FLOW =====
Show today's schedule → user picks → confirm → if YES:
ACTION:CANCEL_APPOINTMENT:{{"appointment_id":<id>}}

===== CREATE PATIENT FLOW =====
When user says "create patient", "add patient", "new patient":
Ask ONE BY ONE:
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

After all → show summary → ask confirm:
"Patient Summary:
👤 Name: [name]
📞 Phone: [phone]
📧 Email: [email]
⚧ Gender: [gender]
🎂 DOB: [dob]
🏙 City: [city]
🌍 Country: [country]
🩸 Blood: [blood]
⚠️ Allergies: [allergies]
💆 Skin: [skin]
Confirm? Reply YES to create."

If YES → on ONE line:
ACTION:CREATE_PATIENT:{{"name":"<n>","phone":"<p>","email":"<e>","gender":"<g>","dob":"<d>","city":"<c>","country":"<co>","blood_type":"<b>","allergies":"<a>","skin_type":"<s>"}}

===== UPDATE PATIENT FLOW =====
When user says "update/change/edit patient [field]":
1. Find patient by NAME from AVAILABLE PATIENTS list — do NOT use list numbers for update
2. Confirm: "Update [field] of [patient name] to [new value]? Reply YES"
3. If YES → use their exact db_id:
ACTION:UPDATE_PATIENT:{{"patient_id":<db_id>,"field":"<field>","value":"<value>"}}
Fields: name, phone, email, gender, dob, city, country, blood_type, allergies, skin_type
IMPORTANT: Always match patient by NAME. Never update the wrong patient.

===== DELETE PATIENT FLOW =====
When user says "delete patient":
1. Show the full patient list as numbered list:
"Which patient do you want to delete?
1. Vini JR
2. Lamine
3. Gonzalo
...
Type a number to select."

2. When user replies with a number → find the patient at that position in the list → get their db_id
3. Show warning with their name:
"⚠️ Are you sure you want to delete [Name]?
This CANNOT be undone. Type YES to confirm."
4. If YES → use their exact db_id from the list:
ACTION:DELETE_PATIENT:{{"patient_id":<db_id>}}
CRITICAL: Use the db_id shown in [db_id:X] from the list — NOT the list number.

===== IMPORTANT RULES =====
- Always show numbered lists before asking
- NUMBER reply → select from last shown list
- "give me [name] phone/number/contact" → show phone ONLY, do NOT start booking
- Keep track of all selections — never re-ask confirmed items
- db_id is numeric id (not Aura6 format)
- price_plan_id: use first price plan id from selected treatment
- ONE action per response on its own line
- Be friendly and concise like a WhatsApp assistant
- Answer ALL questions from ALL roles — no restrictions
"""


def _execute_action(action_line, token):
    try:
        if action_line.startswith("ACTION:GET_SLOTS:"):
            params     = json.loads(action_line.split("ACTION:GET_SLOTS:")[1])
            staff_id   = params.get('staff_id')
            service_id = params.get('service_id')
            month      = params.get('month')

            try:
                import datetime, calendar
                from appointments.models import Appointment
                from users.models import StaffWorkingHours, StaffBreakTime, StaffLeave
                from treatments.models import Treatment
                from django.utils.timezone import localdate, localtime as ltime
                from django.utils import timezone as dj_tz

                year, mon     = map(int, month.split('-'))
                days_in_month = calendar.monthrange(year, mon)[1]
                today_date    = localdate()

                try:
                    duration = Treatment.objects.get(id=service_id).duration
                except:
                    duration = 60

                working_hours = {wh.day: wh for wh in StaffWorkingHours.objects.filter(staff_id=staff_id)}
                if not working_hours:
                    import datetime as dt2
                    for day in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
                        class FakeWH:
                            start_time = dt2.time(9, 0)
                            end_time   = dt2.time(18, 0)
                        working_hours[day] = FakeWH()

                DAY_MAP     = {0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'}
                leaves      = StaffLeave.objects.filter(staff_id=staff_id)
                leave_dates = set()
                for leave in leaves:
                    d = leave.from_date
                    while d <= leave.to_date:
                        leave_dates.add(d)
                        d += datetime.timedelta(days=1)

                breaks      = list(StaffBreakTime.objects.filter(staff_id=staff_id))
                month_start = datetime.date(year, mon, 1)
                month_end   = datetime.date(year, mon, days_in_month)
                bookings    = Appointment.objects.filter(
                    staff_id=staff_id,
                    date_time__date__gte=month_start,
                    date_time__date__lte=month_end,
                    status__in=['upcoming', 'in_session']
                ).values('date_time', 'duration')

                booked_slots = {}
                for b in bookings:
                    appt_dt = b['date_time']
                    if hasattr(appt_dt, 'tzinfo') and appt_dt.tzinfo:
                        appt_dt = ltime(appt_dt).replace(tzinfo=None)
                    d = appt_dt.date()
                    if d not in booked_slots:
                        booked_slots[d] = []
                    booked_slots[d].append((appt_dt.time(), b['duration']))

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

                    if date == today_date:
                        now_time = ltime(dj_tz.now()).replace(tzinfo=None)
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
                        try:
                            from clinic.models import ClinicHours
                            ch = ClinicHours.objects.filter(day=date.strftime('%a'), is_open=True).first()
                            if ch and ch.close_time and slot_end > ch.close_time:
                                cur += datetime.timedelta(minutes=30)
                                continue
                        except:
                            pass
                        blocked = False
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
                from django.utils import timezone as tz

                raw = action_line.split("ACTION:BOOK_APPOINTMENT:")[1].strip()
                try:
                    body = json.loads(raw)
                except:
                    body = {}
                    for key in ['patient_id','staff_id','treatment_id','room_id','price_plan_id']:
                        m = re.search(rf'"{key}"\s*:\s*(\d+)', raw)
                        if m: body[key] = int(m.group(1))
                    for key in ['date','time']:
                        m = re.search(rf'"{key}"\s*:\s*"([^"]+)"', raw)
                        if m: body[key] = m.group(1)

                patient   = Patient.objects.get(id=body['patient_id'])
                staff     = StaffUser.objects.get(id=body['staff_id'])
                treatment = Treatment.objects.get(id=body['treatment_id'])
                room      = Room.objects.get(id=body['room_id'])
                plan      = PricePlan.objects.get(id=body['price_plan_id'])
                date_str  = body['date']
                time_str  = body['time'].split('-')[0].strip()
                dt_aware  = tz.make_aware(datetime.datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M'))

                appt = Appointment.objects.create(
                    patient=patient, staff=staff, treatment=treatment, room_fk=room,
                    price_plan=plan, date_time=dt_aware, duration=treatment.duration,
                    session_number=1, total_sessions=plan.sessions, status='upcoming',
                    payment_status='pending', consent_status='pending', payment_type='cash',
                )
                return {'action': 'BOOK_APPOINTMENT', 'success': True,
                        'message': f"✅ Appointment booked! ID: {appt.id} — {patient.name} on {date_str} at {time_str} with {staff.username}."}
            except Exception as e:
                return {'action': 'BOOK_APPOINTMENT', 'success': False, 'message': f"❌ Booking failed: {str(e)}"}

        elif action_line.startswith("ACTION:CANCEL_APPOINTMENT:"):
            try:
                import re
                from appointments.models import Appointment
                raw = action_line.split("ACTION:CANCEL_APPOINTMENT:")[1]
                try:
                    appt_id = json.loads(raw).get('appointment_id')
                except:
                    m = re.search(r'(\d+)', raw)
                    appt_id = int(m.group(1)) if m else None
                if not appt_id:
                    return {'action': 'CANCEL_APPOINTMENT', 'success': False, 'message': '❌ Could not find appointment ID.'}
                appt = Appointment.objects.get(id=appt_id)
                appt.status = 'cancelled'
                appt.save()
                return {'action': 'CANCEL_APPOINTMENT', 'success': True, 'message': f"✅ Appointment #{appt_id} cancelled."}
            except Exception as e:
                return {'action': 'CANCEL_APPOINTMENT', 'success': False, 'message': f"❌ Cancel failed: {str(e)}"}

        elif action_line.startswith("ACTION:CREATE_PATIENT:"):
            try:
                import re
                from patients.models import Patient

                raw = action_line.split("ACTION:CREATE_PATIENT:")[1].strip()
                try:
                    body = json.loads(raw)
                except:
                    body = {}
                    for key in ['name','phone','email','gender','dob','city','country','blood_type','allergies','skin_type']:
                        m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', raw)
                        if m: body[key] = m.group(1)

                if not body.get('name') or not body.get('phone'):
                    return {'action': 'CREATE_PATIENT', 'success': False, 'message': '❌ Name and phone are required.'}

                def clean(v):
                    return '' if not v or str(v).lower() in ['skip','none',''] else v

                last       = Patient.objects.order_by('-id').first()
                patient_id = f"Aura{(last.id + 1) if last else 1}"

                patient = Patient.objects.create(
                    patient_id = patient_id,
                    name       = body.get('name', ''),
                    phone      = body.get('phone', ''),
                    email      = clean(body.get('email', '')),
                    gender     = clean(body.get('gender', '')),
                    dob        = body.get('dob') if body.get('dob') and str(body.get('dob','')).lower() != 'skip' else None,
                    city       = clean(body.get('city', '')),
                    country    = clean(body.get('country', '')),
                    blood_type = clean(body.get('blood_type', '')),
                    allergies  = clean(body.get('allergies', '')),
                    skin_type  = clean(body.get('skin_type', '')),
                    category   = 'New',
                )
                return {'action': 'CREATE_PATIENT', 'success': True,
                        'message': f"✅ Patient created! {patient.patient_id} — {patient.name}",
                        'data': {'id': patient.id, 'patient_id': patient.patient_id, 'name': patient.name}}
            except Exception as e:
                return {'action': 'CREATE_PATIENT', 'success': False, 'message': f"❌ Failed to create patient: {str(e)}"}

        elif action_line.startswith("ACTION:UPDATE_PATIENT:"):
            try:
                import re
                from patients.models import Patient
                raw = action_line.split("ACTION:UPDATE_PATIENT:")[1].strip()
                try:
                    body = json.loads(raw)
                except:
                    body = {}
                    m = re.search(r'"patient_id"\s*:\s*(\d+)', raw)
                    if m: body['patient_id'] = int(m.group(1))
                    m = re.search(r'"field"\s*:\s*"([^"]+)"', raw)
                    if m: body['field'] = m.group(1)
                    m = re.search(r'"value"\s*:\s*"([^"]+)"', raw)
                    if m: body['value'] = m.group(1)
                patient = Patient.objects.get(id=body['patient_id'])
                setattr(patient, body['field'], body['value'])
                patient.save()
                return {'action': 'UPDATE_PATIENT', 'success': True,
                        'message': f"✅ {patient.name}'s {body['field']} updated to '{body['value']}'."}
            except Exception as e:
                return {'action': 'UPDATE_PATIENT', 'success': False, 'message': f"❌ Update failed: {str(e)}"}

        elif action_line.startswith("ACTION:GET_PATIENT_HISTORY:"):
            try:
                import re
                from appointments.models import Appointment
                from patients.models import Patient
                from django.utils.timezone import localtime as ltime

                raw = action_line.split("ACTION:GET_PATIENT_HISTORY:")[1].strip()
                try:
                    body = json.loads(raw)
                    patient_id = body.get('patient_id')
                except:
                    m = re.search(r'(\d+)', raw)
                    patient_id = int(m.group(1)) if m else None

                patient = Patient.objects.get(id=patient_id)
                appts   = Appointment.objects.filter(patient=patient).select_related('treatment', 'staff').order_by('-date_time')[:20]

                history = []
                for a in appts:
                    dt = ltime(a.date_time) if a.date_time else None
                    history.append({
                        'date':           dt.strftime('%Y-%m-%d') if dt else '',
                        'time':           dt.strftime('%H:%M') if dt else '',
                        'treatment':      a.treatment.name if a.treatment else '',
                        'therapist':      a.staff.username if a.staff else '',
                        'status':         a.status,
                        'payment_status': a.payment_status,
                        'amount':         f"€{a.payment_amount}" if a.payment_amount else '€0',
                    })

                return {
                    'action':  'GET_PATIENT_HISTORY',
                    'success': True,
                    'patient': patient.name,
                    'data':    history,
                    'message': f"Found {len(history)} appointments for {patient.name}"
                }
            except Exception as e:
                return {'action': 'GET_PATIENT_HISTORY', 'success': False, 'message': f"❌ Error: {str(e)}"}
            try:
                import re
                from patients.models import Patient
                raw = action_line.split("ACTION:DELETE_PATIENT:")[1].strip()
                try:
                    patient_id = json.loads(raw).get('patient_id')
                except:
                    m = re.search(r'(\d+)', raw)
                    patient_id = int(m.group(1)) if m else None
                patient = Patient.objects.get(id=patient_id)
                name = patient.name
                patient.delete()
                return {'action': 'DELETE_PATIENT', 'success': True, 'message': f"✅ Patient {name} deleted successfully."}
            except Exception as e:
                return {'action': 'DELETE_PATIENT', 'success': False, 'message': f"❌ Delete failed: {str(e)}"}

    except Exception as e:
        return {'action': 'ERROR', 'message': str(e)}

    return None


class AIChatView(APIView):
    """
    POST /api/ai/chat/
    Body: { "message": "...", "conversation_history": [] }
    All roles — admin, therapist, reception — get full access.
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
            context = {
                'role': getattr(user, 'role', ''), 'name': user.username,
                'today': str(timezone.localdate()), 'patients': [],
                'therapists': [], 'treatments': [], 'rooms': []
            }

        system_prompt = _build_system_prompt(user, context)

        groq_messages = [{'role': 'system', 'content': system_prompt}]
        for h in history:
            if h.get('role') == 'user':
                groq_messages.append({'role': 'user', 'content': h['content']})
            elif h.get('role') == 'assistant':
                groq_messages.append({'role': 'assistant', 'content': h['content']})
        groq_messages.append({'role': 'user', 'content': message})

        def _call_groq(messages, api_key):
            for attempt in range(4):
                try:
                    resp = requests.post(
                        GROQ_API_URL,
                        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                        json={'model': GROQ_MODEL, 'messages': messages, 'max_tokens': 1024, 'temperature': 0.3},
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        return resp.status_code, resp
                    elif resp.status_code == 429:
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
            if status_code != 200 or response is None:
                return Response({'error': 'AI service error.'}, status=503)

            data  = response.json()
            reply = data['choices'][0]['message']['content']

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
                        options_result = json.loads(line_stripped.split('SHOW_OPTIONS:')[1])
                        clean_reply    = reply.replace(line, '').strip()
                    except:
                        pass
                    break

            # ── Execute action — no token required ───────────────────────────
            if action_line:
                action_result = _execute_action(action_line, token)

                if action_result and action_result.get('action') == 'GET_SLOTS':
                    slot_data = action_result.get('data', {})
                    if not slot_data:
                        follow_up = "No available slots this month. Tell the user to try a different therapist or next month."
                    else:
                        follow_up = f"""Available slots:
{json.dumps(slot_data, indent=2)}
Show available DATES as numbered list with slot count. Ask which date."""

                    groq_messages.append({'role': 'assistant', 'content': clean_reply})
                    groq_messages.append({'role': 'user', 'content': follow_up})
                    status_code2, response2 = _call_groq(groq_messages, api_key)
                    if status_code2 == 200 and response2:
                        clean_reply = response2.json()['choices'][0]['message']['content']
                        for line in clean_reply.split('\n'):
                            if line.strip().startswith('SHOW_OPTIONS:'):
                                try:
                                    options_result = json.loads(line.strip().split('SHOW_OPTIONS:')[1])
                                    clean_reply    = clean_reply.replace(line, '').strip()
                                except:
                                    pass
                                break

                elif action_result and action_result.get('action') in [
                    'BOOK_APPOINTMENT', 'CANCEL_APPOINTMENT',
                    'CREATE_PATIENT', 'UPDATE_PATIENT', 'DELETE_PATIENT'
                ]:
                    msg = action_result.get('message', '')
                    clean_reply = msg if action_result.get('success') else f"{clean_reply}\n\n{msg}".strip()

                elif action_result and action_result.get('action') == 'GET_PATIENT_HISTORY':
                    if action_result.get('success'):
                        history_data = action_result.get('data', [])
                        patient_name = action_result.get('patient', '')
                        follow_up = f"""Patient history data for {patient_name}:
{json.dumps(history_data, indent=2)}
Show this as a formatted list:
"📋 {patient_name}'s Appointment History:
1. [Date] [Time] — [Treatment] with [Therapist] — [Status] — [Amount]
..."
If empty say "No appointments found for {patient_name}."
"""
                        groq_messages.append({'role': 'assistant', 'content': clean_reply})
                        groq_messages.append({'role': 'user', 'content': follow_up})
                        status_code2, response2 = _call_groq(groq_messages, api_key)
                        if status_code2 == 200 and response2:
                            clean_reply = response2.json()['choices'][0]['message']['content']
                    else:
                        clean_reply = action_result.get('message', '❌ Could not fetch history.')

            if not clean_reply and options_result:
                clean_reply = options_result.get('question', 'Please choose an option:')
            elif not clean_reply and action_result:
                clean_reply = action_result.get('message', '✅ Done!')
            elif not clean_reply:
                clean_reply = 'Sorry, I could not process that.'

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