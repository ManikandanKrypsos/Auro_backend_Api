from django.utils import timezone
from rest_framework import serializers
from .models import Appointment
from users.models import User
from patients.models import Patient
from treatments.models import Treatment, PricePlan
from rooms.models import Room
import datetime

STATUS_MAP = {
    1: 'upcoming',
    2: 'in_session',
    3: 'completed',
    4: 'cancelled',
    5: 'no_show',
}
PAYMENT_STATUS_MAP = {
    1: 'pending',
    2: 'paid',
    3: 'refunded',
}
PAYMENT_TYPE_MAP = {
    1: 'online',
    2: 'cash',
}
CONSENT_STATUS_MAP = {
    1: 'pending',
    2: 'signed',
}



class AppointmentSerializer(serializers.ModelSerializer):
    """Full read serializer with all nested objects."""

    # Package
    package_id         = serializers.SerializerMethodField()
    package_detail     = serializers.SerializerMethodField()

    # Date and time split
    date               = serializers.SerializerMethodField()
    time               = serializers.SerializerMethodField()

    # Status IDs
    status_id          = serializers.SerializerMethodField()
    consent_status_id  = serializers.SerializerMethodField()
    payment_status_id  = serializers.SerializerMethodField()
    payment_type_id    = serializers.SerializerMethodField()

    # Patient
    patient_detail = serializers.SerializerMethodField()
    # Staff
    staff_detail   = serializers.SerializerMethodField()
    # Treatment
    treatment_detail = serializers.SerializerMethodField()
    # Room
    room_detail    = serializers.SerializerMethodField()

    class Meta:
        model  = Appointment
        fields = [
            'id',
            'patient_detail',
            'staff_detail',
            'treatment_detail',
            'room_detail',
            'date', 'time', 'duration',
            'session_number', 'total_sessions',
            'package_id', 'package_detail',
            'status', 'status_id',
            'patient_arrived',
            'consent_status', 'consent_status_id', 'consent_form_url',
            'payment_amount',
            'payment_status', 'payment_status_id',
            'payment_type', 'payment_type_id',
            'notes',
            'updated_at',
        ]

    def get_patient_detail(self, obj):
        p = obj.patient
        age = None
        if p.dob:
            today = datetime.date.today()
            age   = today.year - p.dob.year - ((today.month, today.day) < (p.dob.month, p.dob.day))
        # Last visit
        last = Appointment.objects.filter(
            patient=p, status='completed'
        ).exclude(id=obj.id).order_by('-date_time').first()
        return {
            'id':           p.id,
            'patient_id':   p.patient_id,
            'name':         p.name,
            'phone':        p.phone,
            'email':        p.email,
            'gender':       p.gender,
            'age':          age,
            'image':        p.image or None,
            'last_visit':   {
                'date':      str(last.date_time.date()) if last else None,
                'treatment': last.treatment.name if last else None,
            }
        }

    def get_staff_detail(self, obj):
        s = obj.staff
        return {
            'id':            s.id,
            'name':          s.username or s.email.split('@')[0],
            'role':          s.role,
            'specialist_area': s.specialist_area,
            'profile_image': s.profile_image or None,
        }

    def get_treatment_detail(self, obj):
        t    = obj.treatment
        plan = obj.price_plan
        return {
            'id':           t.id,
            'name':         t.name,
            'duration':     obj.duration,
            'category':     t.category,
            'price':        str(plan.price) if plan else str(obj.payment_amount or ''),
            'price_plan_id': plan.id if plan else None,
            'sessions':     plan.sessions if plan else obj.total_sessions,
        }

    def get_package_id(self, obj):
        return obj.package_id if obj.package_id else None

    def get_package_detail(self, obj):
        if not obj.package_id:
            return None
        pkg = obj.package
        if not pkg:
            return None
        return {
            'id':                  pkg.id,
            'total_sessions':      pkg.total_sessions,
            'sessions_completed':  pkg.sessions_completed,
            'sessions_remaining':  pkg.sessions_remaining,
            'status':              pkg.status,
            'status_id':           pkg.status_id,
        }

    def get_date(self, obj):
        if obj.date_time:
            from django.utils import timezone as tz
            dt = tz.localtime(obj.date_time) if tz.is_aware(obj.date_time) else obj.date_time
            return str(dt.date())
        return None

    def get_time(self, obj):
        if obj.date_time:
            import datetime
            from django.utils import timezone as tz
            dt       = tz.localtime(obj.date_time) if tz.is_aware(obj.date_time) else obj.date_time
            start    = dt.strftime('%H:%M')
            end_dt   = dt + datetime.timedelta(minutes=obj.duration or 0)
            end      = end_dt.strftime('%H:%M')
            return f"{start} - {end}"
        return None

    def get_status_id(self, obj):
        return {'upcoming':1,'in_session':2,'completed':3,'cancelled':4}.get(obj.status)

    def get_consent_status_id(self, obj):
        return {'pending':1,'signed':2}.get(obj.consent_status)

    def get_payment_status_id(self, obj):
        return {'pending':1,'paid':2,'refunded':3}.get(obj.payment_status)

    def get_payment_type_id(self, obj):
        return {'online':1,'cash':2}.get(obj.payment_type)

    def get_room_detail(self, obj):
        if not obj.room_fk:
            return None
        return {
            'id':         obj.room_fk.id,
            'name':       obj.room_fk.name,
            'room_type':  obj.room_fk.room_type,
        }


class AppointmentWriteSerializer(serializers.Serializer):
    """
    Used for POST and PATCH.

    Body:
    {
        "patient_id":      1,
        "staff_id":        8,
        "treatment_id":    3,
        "room_id":         1,          // optional
        "price_plan_id":   2,          // optional
        "date_time":       "2026-04-30T09:00:00",
        "duration":        60,
        "session_number":  1,
        "total_sessions":  3,
        "status":          "upcoming",
        "payment_amount":  400.00,
        "payment_status":  "paid",
        "payment_type":    "package",  // single | package
        "notes":           "Patient prefers evening slots.",
        "consent_status":  "pending"
    }
    """
    patient_id      = serializers.CharField(required=False)  # accepts DB id (41) or patient_id (Aura41)
    staff_id        = serializers.IntegerField(required=False)
    treatment_id    = serializers.IntegerField(required=False)
    room_id         = serializers.IntegerField(required=False, allow_null=True)
    price_plan_id   = serializers.IntegerField(required=False, allow_null=True)
    date            = serializers.DateField(required=False)
    time            = serializers.CharField(required=False)  # e.g. "9:00" or "14:30"
    duration        = serializers.IntegerField(min_value=1, required=False)
    session_number  = serializers.IntegerField(min_value=1, required=False)
    total_sessions  = serializers.IntegerField(min_value=1, required=False)
    status_id        = serializers.IntegerField(required=False)
    patient_arrived  = serializers.BooleanField(required=False)
    consent_status_id = serializers.IntegerField(required=False)
    consent_form_url = serializers.URLField(required=False, allow_blank=True)
    payment_amount   = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    payment_status_id = serializers.IntegerField(required=False)
    payment_type_id  = serializers.IntegerField(required=False)
    notes           = serializers.CharField(required=False, allow_blank=True)

    def validate_patient_id(self, value):
        # Try integer DB id first, then patient_id string
        try:
            if Patient.objects.filter(id=int(value)).exists():
                return value
        except (ValueError, TypeError):
            pass
        if Patient.objects.filter(patient_id=value).exists():
            return value
        raise serializers.ValidationError(f"Patient '{value}' not found.")

    def validate_status_id(self, value):
        if value not in STATUS_MAP:
            raise serializers.ValidationError("Invalid status_id. Use 1=Upcoming, 2=Completed, 3=Cancelled, 4=No Show.")
        return value

    def validate_payment_status_id(self, value):
        if value not in PAYMENT_STATUS_MAP:
            raise serializers.ValidationError("Invalid payment_status_id. Use 1=Pending, 2=Paid, 3=Refunded.")
        return value

    def validate_payment_type_id(self, value):
        if value not in PAYMENT_TYPE_MAP:
            raise serializers.ValidationError("Invalid payment_type_id. Use 1=Online Payment, 2=Cash.")
        return value

    def validate_consent_status_id(self, value):
        if value not in CONSENT_STATUS_MAP:
            raise serializers.ValidationError("Invalid consent_status_id. Use 1=Pending, 2=Signed.")
        return value

    def validate_staff_id(self, value):
        if not User.objects.filter(id=value, role__in=['therapist','reception']).exists():
            raise serializers.ValidationError("Staff not found.")
        return value

    def validate_treatment_id(self, value):
        if not Treatment.objects.filter(id=value).exists():
            raise serializers.ValidationError("Treatment not found.")
        return value

    def validate_room_id(self, value):
        if value and not Room.objects.filter(id=value).exists():
            raise serializers.ValidationError("Room not found.")
        return value

    def validate_price_plan_id(self, value):
        if value and not PricePlan.objects.filter(id=value).exists():
            raise serializers.ValidationError("Price plan not found.")
        return value

    def _save(self, instance, validated_data):
        patient_id    = validated_data.pop('patient_id', None)
        staff_id      = validated_data.pop('staff_id', None)
        treatment_id  = validated_data.pop('treatment_id', None)
        room_id       = validated_data.pop('room_id', None)
        price_plan_id = validated_data.pop('price_plan_id', None)
        # ID fields handled below

        # Resolve treatment early so duration is available for slot conflict check
        treatment_obj = None
        if treatment_id:
            treatment_obj = Treatment.objects.get(id=treatment_id)
            validated_data['treatment'] = treatment_obj

        # Map IDs to values
        status_id         = validated_data.pop('status_id', None)
        payment_status_id = validated_data.pop('payment_status_id', None)
        payment_type_id   = validated_data.pop('payment_type_id', None)
        consent_status_id = validated_data.pop('consent_status_id', None)

        if status_id:
            validated_data['status'] = STATUS_MAP[status_id]
        if payment_status_id:
            validated_data['payment_status'] = PAYMENT_STATUS_MAP[payment_status_id]
        if payment_type_id:
            validated_data['payment_type'] = PAYMENT_TYPE_MAP[payment_type_id]
        if consent_status_id:
            validated_data['consent_status'] = CONSENT_STATUS_MAP[consent_status_id]

        # Combine date + time into date_time
        date     = validated_data.pop('date', None)
        time_str = validated_data.pop('time', None)

        if time_str:
            import datetime as dt
            from django.utils import timezone as tz
            from appointments.models import Appointment as Appt
            from treatments.models import Treatment as Treat

            # Extract start time from range format "09:00 - 10:20" or plain "09:00"
            start_time_str = time_str.strip().split('-')[0].strip()
            parts  = start_time_str.split(':')
            hour   = parts[0].zfill(2)
            minute = parts[1].strip() if len(parts) > 1 else '00'
            parsed_time = dt.datetime.strptime(f"{hour}:{minute}", '%H:%M').time()

            # Use provided date, or fall back to existing date_time date
            if date:
                use_date = date
            elif instance and instance.date_time:
                use_date = tz.localtime(instance.date_time).date() if tz.is_aware(instance.date_time) else instance.date_time.date()
            else:
                use_date = dt.date.today()

            # Reject past dates
            if use_date < dt.date.today():
                raise serializers.ValidationError({
                    'date': f'{use_date} is in the past. Please choose today or a future date.'
                })

            new_start = tz.make_aware(dt.datetime.combine(use_date, parsed_time))

            # Get duration from treatment or existing appointment
            duration = None
            if treatment_obj:
                duration = treatment_obj.duration
            elif instance:
                duration = instance.duration
            if not duration:
                duration = 60
            new_end = new_start + dt.timedelta(minutes=duration)

            # Check staff conflict
            staff = validated_data.get('staff') or (instance.staff if instance else None)
            if staff:
                qs = Appt.objects.filter(
                    staff=staff,
                    date_time__date=use_date,
                    status='upcoming'
                )
                if instance:
                    qs = qs.exclude(pk=instance.pk)
                for appt in qs:
                    appt_start = appt.date_time.replace(tzinfo=None) if not tz.is_aware(appt.date_time) else appt.date_time
                    appt_end   = appt_start + dt.timedelta(minutes=appt.duration or duration)
                    ns = new_start.replace(tzinfo=None) if tz.is_naive(new_start) else new_start
                    ne = new_end.replace(tzinfo=None) if tz.is_naive(new_end) else new_end
                    if not (ne <= appt_start or ns >= appt_end):
                        raise serializers.ValidationError({
                            'time': f'This slot ({hour}:{minute}) is already booked for the selected therapist. Please choose another time.'
                        })

            # Check room conflict
            room = validated_data.get('room_fk') or (instance.room_fk if instance else None)
            if room:
                qs = Appt.objects.filter(
                    room_fk=room,
                    date_time__date=use_date,
                    status='upcoming'
                )
                if instance:
                    qs = qs.exclude(pk=instance.pk)
                for appt in qs:
                    appt_start = appt.date_time.replace(tzinfo=None) if not tz.is_aware(appt.date_time) else appt.date_time
                    appt_end   = appt_start + dt.timedelta(minutes=appt.duration or duration)
                    ns = new_start.replace(tzinfo=None) if tz.is_naive(new_start) else new_start
                    ne = new_end.replace(tzinfo=None) if tz.is_naive(new_end) else new_end
                    if not (ne <= appt_start or ns >= appt_end):
                        raise serializers.ValidationError({
                            'time': f'This slot ({hour}:{minute}) is already booked for the selected room. Please choose another time.'
                        })

            validated_data['date_time'] = new_start

        elif date:
            # Only date changed, keep existing time
            import datetime as dt
            from django.utils import timezone as tz
            if instance and instance.date_time:
                existing_time = tz.localtime(instance.date_time).time()
            else:
                existing_time = dt.time(9, 0)
            validated_data['date_time'] = tz.make_aware(dt.datetime.combine(date, existing_time))

        package_id = validated_data.pop('package_id', None)
        if package_id:
            try:
                from packages.models import PatientPackage
                pkg = PatientPackage.objects.get(id=package_id)
                validated_data['package'] = pkg
                # Auto-calculate session number
                existing = Appointment.objects.filter(package=pkg).count()
                validated_data['session_number'] = existing + 1
                validated_data['total_sessions'] = pkg.total_sessions
            except Exception:
                pass

        if patient_id:
            try:
                validated_data['patient'] = Patient.objects.get(id=patient_id)
            except (Patient.DoesNotExist, ValueError):
                validated_data['patient'] = Patient.objects.get(patient_id=patient_id)
        if staff_id:
            validated_data['staff'] = User.objects.get(id=staff_id)
        # treatment already set above via treatment_obj
        if treatment_obj and 'duration' not in validated_data:
            validated_data['duration'] = treatment_obj.duration
        if room_id is not None:
            validated_data['room_fk'] = Room.objects.get(id=room_id) if room_id else None
        if price_plan_id is not None:
            validated_data['price_plan'] = PricePlan.objects.get(id=price_plan_id) if price_plan_id else None

        if instance is None:
            return Appointment.objects.create(**validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def create(self, validated_data):
        return self._save(None, validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)


class AvailableSlotsSerializer(serializers.Serializer):
    """
    GET /api/appointments/available-slots/
    ?staff_id=8&date=2026-04-30&duration=60
    """
    staff_id = serializers.IntegerField()
    date     = serializers.DateField()
    duration = serializers.IntegerField(default=60)