from rest_framework import serializers
from .models import Treatment, PricePlan
from users.models import User
from rooms.models import Room

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
    price_plans     = PricePlanSerializer(many=True, read_only=True)
    staffs                = serializers.SerializerMethodField()
    category_id           = serializers.SerializerMethodField()
    rooms_detail          = serializers.SerializerMethodField()
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
            'rooms_detail',
            'staffs',
            'recommended_frequency_value',
            'recommended_frequency_unit', 'recommended_frequency_unit_id',
            'created_at', 'updated_at',
        ]

    def get_staff_ids(self, obj):
        return list(obj.staff.values_list('id', flat=True))

    def get_category_id(self, obj):
        return CATEGORY_ID_MAP.get(obj.category)

    def get_recommended_frequency_unit_id(self, obj):
        return FREQUENCY_UNIT_ID_MAP.get(obj.recommended_frequency_unit)

    def get_staffs(self, obj):
        return [
            {
                'staff_id':   s.id,
                'staff_name': s.username or s.email.split('@')[0],
                'staff_role': s.role,
                'staff_email': s.email,
                'profile_image': s.profile_image or None,
            }
            for s in obj.staff.all()
        ]

    def get_rooms_detail(self, obj):
        return [
            {
                'room_id':    r.id,
                'room_name':  r.name,
                'room_type':  r.room_type,
                'room_type_label': dict(Room.ROOM_TYPE_CHOICES).get(r.room_type, r.room_type),
            }
            for r in obj.rooms.all()
        ]


class TreatmentWriteSerializer(serializers.Serializer):
    name                          = serializers.CharField(max_length=100, required=False)
    category_id                   = serializers.IntegerField(required=False)
    description                   = serializers.CharField(required=False, allow_blank=True)
    duration                      = serializers.IntegerField(min_value=1, required=False)
    image_url                     = serializers.URLField(required=False, allow_blank=True)
    price_plans                   = PricePlanSerializer(many=True, required=False)
    pre_care_instructions         = serializers.CharField(required=False, allow_blank=True)
    post_care_instructions        = serializers.CharField(required=False, allow_blank=True)
    contraindications             = serializers.ListField(child=serializers.CharField(), required=False)
    room_ids                      = serializers.ListField(child=serializers.IntegerField(), required=False)
    room_id                       = serializers.IntegerField(required=False, allow_null=True)  # singular alias
    staff_ids                     = serializers.ListField(child=serializers.IntegerField(), required=False)
    recommended_frequency_value   = serializers.IntegerField(required=False, allow_null=True)
    recommended_frequency_unit_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_category_id(self, value):
        if value not in CATEGORY_MAP:
            raise serializers.ValidationError("Invalid category_id. Use 1=Face, 2=Body.")
        return value

    def validate_room_ids(self, value):
        existing = Room.objects.filter(id__in=value)
        if existing.count() != len(value):
            raise serializers.ValidationError("One or more room IDs are invalid.")
        return value

    def validate_room_id(self, value):
        if value is not None and not Room.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Room with id {value} does not exist.")
        return value

    def validate_recommended_frequency_unit_id(self, value):
        if value is not None and value not in FREQUENCY_UNIT_MAP:
            raise serializers.ValidationError("Invalid recommended_frequency_unit_id. Use 1=Days, 2=Weeks, 3=Months.")
        return value

    def validate_staff_ids(self, value):
        existing = User.objects.filter(id__in=value, role__in=['therapist', 'reception'])
        if existing.count() != len(value):
            raise serializers.ValidationError("One or more staff IDs are invalid.")
        return value

    def _save(self, instance, validated_data):
        price_plans_data = validated_data.pop('price_plans', None)
        staff_ids        = validated_data.pop('staff_ids', None)
        category_id      = validated_data.pop('category_id', None)
        room_ids         = validated_data.pop('room_ids', None)
        room_id          = validated_data.pop('room_id', None)
        freq_unit_id     = validated_data.pop('recommended_frequency_unit_id', None)

        if category_id is not None:
            validated_data['category'] = CATEGORY_MAP[category_id]
        # Support singular room_id as alias for room_ids
        if room_id is not None and room_ids is None:
            room_ids = [room_id]
        if freq_unit_id is not None:
            validated_data['recommended_frequency_unit'] = FREQUENCY_UNIT_MAP[freq_unit_id]

        if instance is None:
            instance = Treatment.objects.create(**validated_data)
        else:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        if price_plans_data is not None:
            instance.price_plans.all().delete()
            for pp in price_plans_data:
                PricePlan.objects.create(treatment=instance, **pp)

        if staff_ids is not None:
            instance.staff.set(staff_ids)

        if room_ids is not None:
            instance.rooms.set(room_ids)

        return instance

    def create(self, validated_data):
        return self._save(None, validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)