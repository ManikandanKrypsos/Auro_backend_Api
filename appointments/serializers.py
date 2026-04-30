from rest_framework import serializers
from .models import Appointment
from users.models import User
from patients.models import Patient
from treatments.models import Treatment, PricePlan
from rooms.models import Room
import datetime


class AppointmentSerializer(serializers.ModelSerializer):
    """Full read serializer with all nested objects."""

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
            'date_time', 'duration',
            'session_number', 'total_sessions',
            'status', 'patient_arrived',
            'consent_status', 'consent_form_url',
            'payment_amount', 'payment_status', 'payment_type',
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
        t = obj.treatment
        plan = obj.price_plan
        return {
            'id':       t.id,
            'name':     t.name,
            'duration': obj.duration,
            'category': t.category,
            'price':    str(plan.price) if plan else str(obj.payment_amount or ''),
            'sessions': plan.sessions if plan else obj.total_sessions,
        }

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
    patient_id      = serializers.IntegerField(required=False)
    staff_id        = serializers.IntegerField(required=False)
    treatment_id    = serializers.IntegerField(required=False)
    room_id         = serializers.IntegerField(required=False, allow_null=True)
    price_plan_id   = serializers.IntegerField(required=False, allow_null=True)
    date_time       = serializers.DateTimeField(required=False)
    duration        = serializers.IntegerField(min_value=1, required=False)
    session_number  = serializers.IntegerField(min_value=1, required=False)
    total_sessions  = serializers.IntegerField(min_value=1, required=False)
    status          = serializers.ChoiceField(
                        choices=['upcoming','completed','cancelled','no_show'],
                        required=False
                      )
    patient_arrived = serializers.BooleanField(required=False)
    consent_status  = serializers.ChoiceField(choices=['pending','signed'], required=False)
    consent_form_url = serializers.URLField(required=False, allow_blank=True)
    payment_amount  = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    payment_status  = serializers.ChoiceField(choices=['pending','paid','refunded'], required=False)
    payment_type    = serializers.ChoiceField(choices=['single','package'], required=False)
    notes           = serializers.CharField(required=False, allow_blank=True)

    def validate_patient_id(self, value):
        if not Patient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Patient not found.")
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

        if patient_id:
            validated_data['patient']    = Patient.objects.get(id=patient_id)
        if staff_id:
            validated_data['staff']      = User.objects.get(id=staff_id)
        if treatment_id:
            t = Treatment.objects.get(id=treatment_id)
            validated_data['treatment']  = t
            # Auto-set duration from treatment if not provided
            if 'duration' not in validated_data:
                validated_data['duration'] = t.duration
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