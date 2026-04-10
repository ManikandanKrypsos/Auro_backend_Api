from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

def send_whatsapp(to_number, message):
    """Send WhatsApp message via Twilio."""
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=f'whatsapp:+{to_number}',
            body=message
        )
        print(f"WhatsApp sent to {to_number}")
    except Exception as e:
        print(f"WhatsApp error: {e}")

def send_email_reminder(to_email, subject, message):
    """Send email via Django email backend."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Email error: {e}")


# ── Tasks ──────────────────────────────────────────────────────────────

@shared_task
def send_booking_confirmation(appointment_id):
    """Fires immediately when an appointment is created."""
    from .models import Appointment
    try:
        appt = Appointment.objects.get(id=appointment_id)
        patient = appt.patient
        treatment = appt.treatment
        date_str = appt.date_time.strftime('%d %b %Y at %I:%M %p')

        message = (
            f"Hi {patient.name}! 💆‍♀️\n\n"
            f"Your appointment at Aura Clinic is confirmed!\n"
            f"📅 {date_str}\n"
            f"💉 Treatment: {treatment.name}\n"
            f"📍 Room: {appt.room}\n\n"
            f"See you soon! ✨\n"
            f"— Aura Clinic"
        )

        if patient.phone:
            send_whatsapp(patient.phone, message)
        if patient.email:
            send_email_reminder(
                patient.email,
                subject=f"Appointment Confirmed — {treatment.name}",
                message=message
            )
    except Appointment.DoesNotExist:
        pass


@shared_task
def send_reminder_24h(appointment_id):
    """Fires 24 hours before the appointment."""
    from .models import Appointment
    try:
        appt = Appointment.objects.get(id=appointment_id)
        patient = appt.patient
        date_str = appt.date_time.strftime('%d %b %Y at %I:%M %p')

        message = (
            f"Hi {patient.name}! ⏰\n\n"
            f"Reminder: you have an appointment TOMORROW at Aura Clinic.\n"
            f"📅 {date_str}\n"
            f"💉 {appt.treatment.name}\n\n"
            f"{appt.treatment.pre_care or ''}\n\n"
            f"Questions? Reply to this message. See you soon! 🌿"
        )

        if patient.phone:
            send_whatsapp(patient.phone, message)
        if patient.email:
            send_email_reminder(
                patient.email,
                subject="See you tomorrow! — Aura Clinic",
                message=message
            )
    except Appointment.DoesNotExist:
        pass


@shared_task
def send_reminder_2h(appointment_id):
    """Fires 2 hours before the appointment."""
    from .models import Appointment
    try:
        appt = Appointment.objects.get(id=appointment_id)
        patient = appt.patient
        date_str = appt.date_time.strftime('%I:%M %p')

        message = (
            f"Hi {patient.name}! 👋\n\n"
            f"Your Aura Clinic appointment is in 2 hours at {date_str}.\n"
            f"💉 {appt.treatment.name} — Room {appt.room}\n\n"
            f"See you very soon! ✨"
        )

        if patient.phone:
            send_whatsapp(patient.phone, message)
    except Appointment.DoesNotExist:
        pass


@shared_task
def send_post_treatment_followup(appointment_id):
    """Fires 3 days after the appointment."""
    from .models import Appointment
    try:
        appt = Appointment.objects.get(id=appointment_id)
        patient = appt.patient

        message = (
            f"Hi {patient.name}! 🌸\n\n"
            f"How are you feeling after your {appt.treatment.name} session?\n\n"
            f"{appt.treatment.post_care or 'We hope you are feeling great!'}\n\n"
            f"Ready to book your next session? Reply here and we will sort it out! 💆‍♀️\n"
            f"— Aura Clinic"
        )

        if patient.phone:
            send_whatsapp(patient.phone, message)
        if patient.email:
            send_email_reminder(
                patient.email,
                subject=f"How are you feeling? — Aura Clinic",
                message=message
            )
    except Appointment.DoesNotExist:
        pass


@shared_task
def send_rebooking_reminder(appointment_id):
    """Fires 30 days after the appointment."""
    from .models import Appointment
    try:
        appt = Appointment.objects.get(id=appointment_id)
        patient = appt.patient

        message = (
            f"Hi {patient.name}! ✨\n\n"
            f"It has been a month since your {appt.treatment.name} at Aura Clinic.\n\n"
            f"Time for your next session? Book now and keep glowing! 💆‍♀️\n"
            f"— Aura Clinic"
        )

        if patient.phone:
            send_whatsapp(patient.phone, message)
        if patient.email:
            send_email_reminder(
                patient.email,
                subject="Time for your next session! — Aura Clinic",
                message=message
            )
    except Appointment.DoesNotExist:
        pass