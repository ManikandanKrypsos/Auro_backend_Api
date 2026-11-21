from rest_framework import serializers
from .models import Lead, LeadActivity

SOURCE_MAP = {
    1: 'instagram',
    2: 'web',
    3: 'walk_in',
    4: 'referral',
    5: 'whatsapp',
    6: 'other',
}
SOURCE_ID_MAP = {v: k for k, v in SOURCE_MAP.items()}

MARKETING_SOURCE_LABELS = {
    'instagram': 'Instagram',
    'web':       'Website',
    'walk_in':   'Walk-in',
    'referral':  'Referral',
    'whatsapp':  'WhatsApp',
    'other':     'Other',
}

STAGE_MAP = {
    1: 'new_inquiries',   # New
    2: 'engaged',         # Contacted
    3: 'consultation',    # Consultation
    5: 'converted',       # Won
    6: 'lost',            # Lost
}
STAGE_ID_MAP = {v: k for k, v in STAGE_MAP.items()}
# Old "Winning" id — accepted for older app versions and treated as Won.
STAGE_MAP[4] = 'converted'
ASSIGNABLE_ROLES = ('admin', 'reception')   # who can own a lead / lead task (they're the roles that can open leads)
STAGE_ID_HELP = "Invalid stage_id. Use 1=New, 2=Contacted, 3=Consultation, 5=Won, 6=Lost"


def scheduled_phones_for(leads):
    """Phones of converted leads whose patient has at least one non-cancelled appointment."""
    from appointments.models import Appointment
    phones = {l.phone for l in leads if l.stage == 'converted' and l.phone}
    if not phones:
        return set()
    return set(
        Appointment.objects.filter(patient__phone__in=phones)
        .exclude(status='cancelled')
        .values_list('patient__phone', flat=True)
    )


def scheduled_patients_for(leads):
    """Ids of converted leads' linked patients that have at least one non-cancelled appointment."""
    from appointments.models import Appointment
    ids = {l.converted_patient_id for l in leads if l.converted_patient_id}
    if not ids:
        return set()
    return set(Appointment.objects.filter(patient_id__in=ids).exclude(status='cancelled')
               .values_list('patient_id', flat=True))


class LeadExtraFieldsMixin:
    """assigned_staff_id + treatment_scheduled, shared by list & detail serializers."""

    def get_assigned_staff_id(self, obj):
        return obj.assigned_to_id

    def get_assigned_staff_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.username or obj.assigned_to.email.split('@')[0]
        return None

    def get_converted_patient_id(self, obj):
        return obj.converted_patient.patient_id if obj.converted_patient_id and obj.converted_patient else None

    def get_converted_patient_name(self, obj):
        return obj.converted_patient.name if obj.converted_patient_id and obj.converted_patient else None

    def get_treatment_scheduled(self, obj):
        # Only meaningful for converted leads; always False otherwise.
        if obj.stage != 'converted':
            return False
        if obj.converted_patient_id:
            patients = self.context.get('scheduled_patients')
            if patients is None:
                patients = scheduled_patients_for([obj])
            return obj.converted_patient_id in patients
        if not obj.phone:
            return False
        phones = self.context.get('scheduled_phones')
        if phones is None:
            phones = scheduled_phones_for([obj])
        return obj.phone in phones


class LeadActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = LeadActivity
        fields = ['id', 'action', 'note', 'created_by_name', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.username or obj.created_by.email.split('@')[0]
        return None


class LeadListSerializer(LeadExtraFieldsMixin, serializers.ModelSerializer):
    marketing_source_id = serializers.SerializerMethodField()
    assigned_staff_id   = serializers.SerializerMethodField()
    treatment_scheduled = serializers.SerializerMethodField()
    stage_id            = serializers.SerializerMethodField()
    service_detail      = serializers.SerializerMethodField()
    assigned_to_name    = serializers.SerializerMethodField()
    assigned_staff_name = serializers.SerializerMethodField()
    converted_patient_id   = serializers.SerializerMethodField()
    converted_patient_name = serializers.SerializerMethodField()

    class Meta:
        model  = Lead
        fields = [
            'id', 'name', 'phone', 'email',
            'source', 'marketing_source_id',
            'stage', 'stage_id',
            'interest', 'service_id', 'service_detail',
            'notes', 'value',
            'assigned_staff_id', 'assigned_staff_name',
            'assigned_to', 'assigned_to_name',            # deprecated aliases of the two above
            'last_contacted', 'next_action_date', 'treatment_scheduled',
            'converted_patient_id', 'converted_patient_name', 'converted_at',
            'created_at', 'updated_at',
        ]

    def get_marketing_source_id(self, obj):
        return SOURCE_ID_MAP.get(obj.source)

    def get_stage_id(self, obj):
        return STAGE_ID_MAP.get(obj.stage)

    def get_service_detail(self, obj):
        if obj.service_id:
            try:
                from treatments.models import Treatment
                t = Treatment.objects.get(id=obj.service_id)
                return {'id': t.id, 'name': t.name, 'duration': t.duration}
            except Exception:
                return None
        return None

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.username or obj.assigned_to.email.split('@')[0]
        return None


class LeadSerializer(LeadExtraFieldsMixin, serializers.ModelSerializer):
    marketing_source_id = serializers.SerializerMethodField()
    assigned_staff_id   = serializers.SerializerMethodField()
    treatment_scheduled = serializers.SerializerMethodField()
    stage_id            = serializers.SerializerMethodField()
    service_detail      = serializers.SerializerMethodField()
    assigned_to_name    = serializers.SerializerMethodField()
    assigned_staff_name = serializers.SerializerMethodField()
    converted_patient_id   = serializers.SerializerMethodField()
    converted_patient_name = serializers.SerializerMethodField()

    class Meta:
        model  = Lead
        fields = [
            'id', 'name', 'phone', 'email',
            'source', 'marketing_source_id',
            'stage', 'stage_id',
            'interest', 'service_id', 'service_detail',
            'notes', 'value',
            'assigned_staff_id', 'assigned_staff_name',
            'assigned_to', 'assigned_to_name',            # deprecated aliases of the two above
            'last_contacted', 'next_action_date', 'treatment_scheduled',
            'converted_patient_id', 'converted_patient_name', 'converted_at',
            'created_at', 'updated_at',
        ]

    def get_marketing_source_id(self, obj):
        return SOURCE_ID_MAP.get(obj.source)

    def get_stage_id(self, obj):
        return STAGE_ID_MAP.get(obj.stage)

    def get_service_detail(self, obj):
        if obj.service_id:
            try:
                from treatments.models import Treatment
                t = Treatment.objects.get(id=obj.service_id)
                return {'id': t.id, 'name': t.name, 'duration': t.duration}
            except Exception:
                return None
        return None

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.username or obj.assigned_to.email.split('@')[0]
        return None


class LeadWriteSerializer(serializers.Serializer):
    """
    POST / PATCH body:
    {
        "name":          "Isabella Sterling",
        "phone":         "+91 99887 76655",
        "email":         "isabella@email.com",
        "marketing_source_id": 1,     // 1=Instagram 2=Web 3=Walk-In 4=Referral 5=WhatsApp 6=Other
        "stage_id":      1,     // 1=New 2=Contacted 3=Consultation 5=Won 6=Lost
        "interest":      "Signature Glow",
        "notes":         "Prefers evening slots",
        "value":         1500.00,
        "service_id":    3,
        "assigned_staff_id": 8,     // canonical; "assigned_to" still accepted (deprecated)
        "next_action_date": "2026-11-07"
    }
    """
    name         = serializers.CharField(max_length=100, required=False, allow_blank=False)
    phone        = serializers.CharField(max_length=20, required=False, allow_blank=False)
    email        = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    marketing_source_id = serializers.IntegerField(required=False)
    service_id          = serializers.IntegerField(required=False, allow_null=True)
    stage_id     = serializers.IntegerField(required=False)
    interest     = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes        = serializers.CharField(required=False, allow_blank=True)
    value        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    assigned_to  = serializers.IntegerField(required=False, allow_null=True)
    assigned_staff_id = serializers.IntegerField(required=False, allow_null=True)  # alias of assigned_to
    next_action_date  = serializers.DateField(required=False, allow_null=True)

    def _validate_staff(self, value):
        if value is not None:
            from users.models import User
            staff = User.objects.filter(id=value, is_active=True).first()
            if staff is None:
                raise serializers.ValidationError(f"Staff member {value} not found.")
            unchanged = self.instance is not None and self.instance.assigned_to_id == staff.id
            if staff.role not in ASSIGNABLE_ROLES and not unchanged:   # older leads may still point at a therapist
                raise serializers.ValidationError(
                    "Leads can only be assigned to an admin or receptionist (therapists can't open leads).")
        return value

    def validate(self, data):
        # creating needs a name and a phone
        if self.instance is None:
            missing = {f: 'This field is required.' for f in ('name', 'phone') if not data.get(f)}
            if missing:
                raise serializers.ValidationError(missing)
        return data

    def validate_assigned_to(self, value):
        return self._validate_staff(value)

    def validate_assigned_staff_id(self, value):
        return self._validate_staff(value)

    def validate_marketing_source_id(self, value):
        if value not in SOURCE_MAP:
            raise serializers.ValidationError(
                "Invalid marketing_source_id. Use 1=Instagram, 2=Web, 3=Walk-In, 4=Referral, 5=WhatsApp, 6=Other"
            )
        return value

    def validate_service_id(self, value):
        if value is not None:
            from treatments.models import Treatment
            if not Treatment.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Service with id {value} not found.")
        return value

    def validate_stage_id(self, value):
        if value not in STAGE_MAP:
            raise serializers.ValidationError(STAGE_ID_HELP)
        return value

    def _save(self, instance, validated_data):
        from users.models import User
        source_id   = validated_data.pop('marketing_source_id', None)
        stage_id    = validated_data.pop('stage_id', None)
        staff_given = 'assigned_to' in validated_data or 'assigned_staff_id' in validated_data
        alias       = validated_data.pop('assigned_staff_id', None)
        assigned_to = validated_data.pop('assigned_to', alias)

        if source_id:
            validated_data['source'] = SOURCE_MAP[source_id]
        if stage_id:
            validated_data['stage'] = STAGE_MAP[stage_id]
        if staff_given:   # null unassigns the lead
            validated_data['assigned_to'] = User.objects.get(id=assigned_to) if assigned_to else None

        if instance is None:
            return Lead.objects.create(**validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def create(self, validated_data):
        return self._save(None, validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)


class LeadStageUpdateSerializer(serializers.Serializer):
    """
    PATCH /api/leads/<id>/stage/
    { "stage_id": 2, "note": "Called and interested" }
    """
    stage_id = serializers.IntegerField()
    note     = serializers.CharField(required=False, allow_blank=True)

    def validate_stage_id(self, value):
        if value not in STAGE_MAP:
            raise serializers.ValidationError(STAGE_ID_HELP)
        return value


class LeadActivityWriteSerializer(serializers.Serializer):
    """
    POST /api/leads/<id>/activity/
    { "action": "call", "note": "Called and confirmed appointment" }
    Action options: call | whatsapp | email | meeting | note
    """
    action = serializers.ChoiceField(choices=['call', 'whatsapp', 'email', 'meeting', 'note'])
    note   = serializers.CharField(required=False, allow_blank=True)