from rest_framework import serializers
from .models import Room

ROOM_TYPE_MAP = {
    1: 'facial_treatment',
    2: 'body_treatment',
}

ROOM_TYPE_ID_MAP = {v: k for k, v in ROOM_TYPE_MAP.items()}


class RoomSerializer(serializers.ModelSerializer):
    room_type_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Room
        fields = ['id', 'name', 'room_type', 'room_type_id', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_room_type_id(self, obj):
        return ROOM_TYPE_ID_MAP.get(obj.room_type)

    def validate_name(self, value):
        instance = self.instance
        if Room.objects.filter(name__iexact=value).exclude(pk=instance.pk if instance else None).exists():
            raise serializers.ValidationError("A room with this name already exists.")
        return value


class RoomCreateUpdateSerializer(serializers.ModelSerializer):
    room_type_id = serializers.IntegerField(write_only=True)

    class Meta:
        model  = Room
        fields = ['name', 'room_type_id', 'description']

    def validate_room_type_id(self, value):
        if value not in ROOM_TYPE_MAP:
            raise serializers.ValidationError("Invalid room_type_id. Use 1=Facial Treatment Room, 2=Body Treatment Room.")
        return value

    def validate_name(self, value):
        instance = self.instance
        if Room.objects.filter(name__iexact=value).exclude(pk=instance.pk if instance else None).exists():
            raise serializers.ValidationError("A room with this name already exists.")
        return value

    def create(self, validated_data):
        room_type_id = validated_data.pop('room_type_id')
        validated_data['room_type'] = ROOM_TYPE_MAP[room_type_id]
        return Room.objects.create(**validated_data)

    def update(self, instance, validated_data):
        room_type_id = validated_data.pop('room_type_id', None)
        if room_type_id is not None:
            instance.room_type = ROOM_TYPE_MAP[room_type_id]
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance