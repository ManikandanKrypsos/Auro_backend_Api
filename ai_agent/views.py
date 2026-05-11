from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import json
import requests


CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL   = "claude-sonnet-4-20250514"


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
        'role': role,
        'name': name,
        'today': str(today),
    }

    if role == 'therapist':
        # Therapist context
        todays_appts = Appointment.objects.filter(
            staff=user, date_time__date=today
        ).select_related('patient', 'treatment')

        context['my_schedule_today'] = [
            {
                'time':        a.date_time.strftime('%H:%M') if a.date_time else None,
                'patient':     a.patient.name if a.patient else None,
                'treatment':   a.treatment.name if a.treatment else None,
                'status':      a.status,
                'duration':    a.duration,
            }
            for a in todays_appts.order_by('date_time')
        ]
        context['total_today']     = todays_appts.count()
        context['completed_today'] = todays_appts.filter(status='completed').count()
        context['in_session']      = todays_appts.filter(status='in_session').exists()
        context['my_patients_count'] = Appointment.objects.filter(
            staff=user
        ).values('patient').distinct().count()

    elif role == 'reception':
        # Reception context
        todays_appts = Appointment.objects.filter(date_time__date=today)
        context['todays_appointments'] = todays_appts.count()
        context['checked_in']          = todays_appts.filter(patient_arrived=True).count()
        context['cancelled_today']     = todays_appts.filter(status='cancelled').count()
        context['total_patients']      = Patient.objects.count()
        context['new_patients_month']  = Patient.objects.filter(
            created_at__gte=now.replace(day=1)
        ).count()
        context['active_leads']        = Lead.objects.filter(
            stage__in=['new_inquiries', 'engaged', 'consultation', 'winning']
        ).count()

    else:
        # Admin context
        from django.db.models import Sum
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        todays_appts   = Appointment.objects.filter(date_time__date=today)
        month_appts    = Appointment.objects.filter(date_time__gte=start_of_month)

        context['todays_appointments']  = todays_appts.count()
        context['monthly_appointments'] = month_appts.count()
        context['total_patients']       = Patient.objects.count()
        context['active_leads']         = Lead.objects.filter(
            stage__in=['new_inquiries', 'engaged', 'consultation', 'winning']
        ).count()
        context['total_leads']          = Lead.objects.count()
        context['revenue_this_month']   = float(
            month_appts.filter(status='completed')
            .aggregate(t=Sum('payment_amount'))['t'] or 0
        )
        context['low_stock_items']      = InventoryItem.objects.filter(
            current_stock__lte=10
        ).count()
        context['total_staff']          = UserModel.objects.filter(
            role__in=['therapist', 'reception'], is_active=True
        ).count()

    return context


def _build_system_prompt(user, context):
    """Build role-specific system prompt with clinic data."""
    role = context.get('role', '')
    name = context.get('name', '')

    base = f"""You are AURA AI, an intelligent assistant for Aura Clinic management system.
You are currently talking to {name}, who is a {role}.
Today's date is {context.get('today')}.

You have access to real-time clinic data provided below.
Be concise, helpful and professional. Use the data to give accurate answers.
If asked about something outside your data, say so honestly.
Never make up patient names, appointment times or financial figures.

CURRENT CLINIC DATA:
{json.dumps(context, indent=2)}
"""

    if role == 'therapist':
        base += """
YOUR ROLE AS THERAPIST ASSISTANT:
- Help with today's schedule and patient sessions
- Suggest treatment notes and skin observations
- Answer questions about patients in your care
- Help track product usage and session completion
- Suggest next treatment recommendations
"""
    elif role == 'reception':
        base += """
YOUR ROLE AS RECEPTION ASSISTANT:
- Help manage appointments and patient inquiries
- Assist with lead tracking and conversion
- Answer patient-related questions
- Help with booking and scheduling queries
- Provide quick stats about today's operations
"""
    else:
        base += """
YOUR ROLE AS ADMIN ASSISTANT:
- Provide business insights and revenue analysis
- Analyze staff performance and appointment trends
- Help with lead pipeline and conversion rates
- Alert about low stock or operational issues
- Suggest improvements based on clinic data
"""

    return base


class AIChatView(APIView):
    """
    POST /api/ai/chat/
    Chat with the Aura AI agent.

    Body:
    {
        "message": "What's my schedule today?",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"}
        ]
    }

    conversation_history is optional — send previous messages for context.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from users.models import User as UserModel

        message  = request.data.get('message', '').strip()
        history  = request.data.get('conversation_history', [])

        if not message:
            return Response({'error': 'message is required.'}, status=400)

        # Get fresh user from DB
        try:
            user = UserModel.objects.get(pk=request.user.pk)
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        # Build context from real clinic data
        try:
            context = _get_clinic_context(user)
        except Exception as e:
            context = {'role': getattr(user, 'role', ''), 'name': user.username, 'today': str(timezone.localdate())}

        system_prompt = _build_system_prompt(user, context)

        # Build messages array
        messages = []
        for h in history:
            if h.get('role') in ['user', 'assistant'] and h.get('content'):
                messages.append({'role': h['role'], 'content': h['content']})

        messages.append({'role': 'user', 'content': message})

        # Call Claude API
        try:
            response = requests.post(
                CLAUDE_API_URL,
                headers={
                    'Content-Type':      'application/json',
                    'anthropic-version': '2023-06-01',
                },
                json={
                    'model':      CLAUDE_MODEL,
                    'max_tokens': 1024,
                    'system':     system_prompt,
                    'messages':   messages,
                },
                timeout=30,
            )

            if response.status_code != 200:
                return Response({
                    'error': 'AI service error. Please try again.',
                    'detail': response.text,
                }, status=503)

            data = response.json()
            reply = data['content'][0]['text']

            return Response({
                'reply':   reply,
                'role':    context.get('role'),
                'context': {
                    'name':  context.get('name'),
                    'today': context.get('today'),
                },
            })

        except requests.Timeout:
            return Response({'error': 'AI response timed out. Please try again.'}, status=504)
        except Exception as e:
            return Response({'error': f'AI service error: {str(e)}'}, status=503)