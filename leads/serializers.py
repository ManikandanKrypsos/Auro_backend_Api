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
    1: 'new_inquiries',
    2: 'engaged',
    3: 'consultation',
    4: 'winning',
    5: 'converted',
    6: 'lost',
}
STAGE_ID_MAP = {v: k for k, v in STAGE_MAP.items()}


class LeadActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = LeadActivity
        fields = ['id', 'action', 'note', 'created_by_name', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.username or obj.created_by.email.split('@')[0]
        return None


class LeadListSerializer(serializers.ModelSerializer):
    marketing_source_id = serializers.SerializerMethodField()
    stage_id            = serializers.SerializerMethodField()
    service_detail      = serializers.SerializerMethodField()
    assigned_to_name    = serializers.SerializerMethodField()

    class Meta:
        model  = Lead
        fields = [
            'id', 'name', 'phone', 'email',
            'source', 'marketing_source_id',
            'stage', 'stage_id',
            'interest', 'service_id', 'service_detail',
            'notes', 'value',
            'assigned_to', 'assigned_to_name',
            'last_contacted',
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


class LeadSerializer(serializers.ModelSerializer):
    marketing_source_id = serializers.SerializerMethodField()
    stage_id            = serializers.SerializerMethodField()
    service_detail      = serializers.SerializerMethodField()
    assigned_to_name    = serializers.SerializerMethodField()

    class Meta:
        model  = Lead
        fields = [
            'id', 'name', 'phone', 'email',
            'source', 'marketing_source_id',
            'stage', 'stage_id',
            'interest', 'service_id', 'service_detail',
            'notes', 'value',
            'assigned_to', 'assigned_to_name',
            'last_contacted',
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
        "source_id":     1,     // 1=Instagram 2=Web 3=Walk-In 4=Referral 5=WhatsApp 6=Other
        "stage_id":      1,     // 1=New Inquiries 2=Engaged 3=Consultation 4=Winning 5=Converted 6=Lost
        "interest":      "Signature Glow",
        "notes":         "Prefers evening slots",
        "value":         1500.00,
        "assigned_to":   8
    }
    """
    name         = serializers.CharField(max_length=100, required=False)
    phone        = serializers.CharField(max_length=20, required=False)
    email        = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    marketing_source_id = serializers.IntegerField(required=False)
    service_id          = serializers.IntegerField(required=False, allow_null=True)
    stage_id     = serializers.IntegerField(required=False)
    interest     = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes        = serializers.CharField(required=False, allow_blank=True)
    value        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    assigned_to  = serializers.IntegerField(required=False, allow_null=True)

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
            raise serializers.ValidationError(
                "Invalid stage_id. Use 1=New Inquiries, 2=Engaged, 3=Consultation, 4=Winning, 5=Converted, 6=Lost"
            )
        return value

    def _save(self, instance, validated_data):
        from users.models import User
        source_id   = validated_data.pop('marketing_source_id', None)
        stage_id    = validated_data.pop('stage_id', None)
        assigned_to = validated_data.pop('assigned_to', None)

        if source_id:
            validated_data['source'] = SOURCE_MAP[source_id]
        if stage_id:
            validated_data['stage'] = STAGE_MAP[stage_id]
        if assigned_to is not None:
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
            raise serializers.ValidationError(
                "Invalid stage_id. Use 1=New Inquiries, 2=Engaged, 3=Consultation, 4=Winning, 5=Converted, 6=Lost"
            )
        return value


class LeadActivityWriteSerializer(serializers.Serializer):
    """
    POST /api/leads/<id>/activity/
    { "action": "call", "note": "Called and confirmed appointment" }
    Action options: call | whatsapp | email | meeting | note
    """
    action = serializers.ChoiceField(choices=['call', 'whatsapp', 'email', 'meeting', 'note'])
    note   = serializers.CharField(required=False, allow_blank=True)