from rest_framework import serializers
from .models import Treatment, PricePlan
from users.models import User

ROOM_TYPE_MAP = {
    1: 'facial_treatment',
    2: 'body_treatment',
}
ROOM_TYPE_ID_MAP = {v: k for k, v in ROOM_TYPE_MAP.items()}

CATEGORY_MAP = {
    1: 'face',
    2: 'body',
}
CATEGORY_ID_MAP = {v: k for k, v in CATEGORY_MAP.items()}

FREQUENCY_UNIT_MAP = {
    1: 'days',
    2: 'weeks',
    3: 'months',
}
FREQUENCY_UNIT_ID_MAP = {v: k for k, v in FREQUENCY_UNIT_MAP.items()}


class PricePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PricePlan
        fields = ['id', 'sessions', 'price']


class TreatmentSerializer(serializers.ModelSerializer):
    """Read serializer — returns full detail with IDs."""
    price_plans  = PricePlanSerializer(many=True, read_only=True)
    staff_ids    = serializers.SerializerMethodField()
    category_id  = serializers.SerializerMethodField()
    room_type_id = serializers.SerializerMethodField()
    recommended_frequency_unit_id = serializers.SerializerMethodField()

    class Meta:
        model  = Treatment
        fields = [
            'id', 'name',
            'category', 'category_id',
            'description', 'duration', 'image_url',
            'price_plans',
            'pre_care_instructions', 'post_care_instructions',
            'contraindications',
            'room_type', 'room_type_id',
            'staff_ids',
            'recommended_frequency_value',
            'recommended_frequency_unit', 'recommended_frequency_unit_id',
            'created_at', 'updated_at',
        ]

    def get_staff_ids(self, obj):
        return list(obj.staff.values_list('id', flat=True))

    def get_category_id(self, obj):
        return CATEGORY_ID_MAP.get(obj.category)

    def get_room_type_id(self, obj):
        return ROOM_TYPE_ID_MAP.get(obj.room_type)

    def get_recommended_frequency_unit_id(self, obj):
        return FREQUENCY_UNIT_ID_MAP.get(obj.recommended_frequency_unit)


class TreatmentWriteSerializer(serializers.Serializer):
    """
    Write serializer — used for POST and PATCH.

    All fields optional for PATCH.

    Body example:
    {
        "name":                          "Detox / Glow",
        "category_id":                   1,           // 1=Face 2=Body
        "description":                   "Describe the therapeutic benefits...",
        "duration":                      60,
        "image_url":                     "https://...",
        "price_plans": [
            { "sessions": 1, "price": 100 },
            { "sessions": 5, "price": 450 }
        ],
        "pre_care_instructions":         "Avoid sun exposure 24h prior...",
        "post_care_instructions":        "Apply SPF 50 daily...",
        "contraindications":             ["Pregnancy", "Active acne"],
        "room_type_id":                  1,           // 1=Facial Treatment Room 2=Body Treatment Room
        "staff_ids":                     [3, 5],
        "recommended_frequency_value":   1,
        "recommended_frequency_unit_id": 2            // 1=Days 2=Weeks 3=Months
    }
    """
    name                          = serializers.CharField(max_length=100, required=False)
    category_id                   = serializers.IntegerField(required=False)
    description                   = serializers.CharField(required=False, allow_blank=True)
    duration                      = serializers.IntegerField(min_value=1, required=False)
    image_url                     = serializers.URLField(required=False, allow_blank=True)
    price_plans                   = PricePlanSerializer(many=True, required=False)
    pre_care_instructions         = serializers.CharField(required=False, allow_blank=True)
    post_care_instructions        = serializers.CharField(required=False, allow_blank=True)
    contraindications             = serializers.ListField(
                                        child=serializers.CharField(), required=False
                                    )
    room_type_id                  = serializers.IntegerField(required=False, allow_null=True)
    staff_ids                     = serializers.ListField(
                                        child=serializers.IntegerField(), required=False
                                    )
    recommended_frequency_value   = serializers.IntegerField(required=False, allow_null=True)
    recommended_frequency_unit_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_category_id(self, value):
        if value not in CATEGORY_MAP:
            raise serializers.ValidationError("Invalid category_id. Use 1=Face, 2=Body.")
        return value

    def validate_room_type_id(self, value):
        if value is not None and value not in ROOM_TYPE_MAP:
            raise serializers.ValidationError("Invalid room_type_id. Use 1=Facial Treatment Room, 2=Body Treatment Room.")
        return value

    def validate_recommended_frequency_unit_id(self, value):
        if value is not None and value not in FREQUENCY_UNIT_MAP:
            raise serializers.ValidationError("Invalid recommended_frequency_unit_id. Use 1=Days, 2=Weeks, 3=Months.")
        return value

    def validate_staff_ids(self, value):
        existing = User.objects.filter(id__in=value, role__in=['therapist', 'reception'])
        if existing.count() != len(value):
            raise serializers.ValidationError("One or more staff IDs are invalid or not therapist/reception.")
        return value

    def _save(self, instance, validated_data):
        price_plans_data = validated_data.pop('price_plans', None)
        staff_ids        = validated_data.pop('staff_ids', None)
        category_id      = validated_data.pop('category_id', None)
        room_type_id     = validated_data.pop('room_type_id', None)
        freq_unit_id     = validated_data.pop('recommended_frequency_unit_id', None)

        if category_id is not None:
            validated_data['category'] = CATEGORY_MAP[category_id]
        if room_type_id is not None:
            validated_data['room_type'] = ROOM_TYPE_MAP[room_type_id]
        elif room_type_id == 0:
            validated_data['room_type'] = ''
        if freq_unit_id is not None:
            validated_data['recommended_frequency_unit'] = FREQUENCY_UNIT_MAP[freq_unit_id]

        if instance is None:
            instance = Treatment.objects.create(**validated_data)
        else:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        # Replace price plans if provided
        if price_plans_data is not None:
            instance.price_plans.all().delete()
            for pp in price_plans_data:
                PricePlan.objects.create(treatment=instance, **pp)

        # Replace staff if provided
        if staff_ids is not None:
            instance.staff.set(staff_ids)

        return instance

    def create(self, validated_data):
        return self._save(None, validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)