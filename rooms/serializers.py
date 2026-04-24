from rest_framework import serializers
from .models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Room
        fields = ['id', 'name', 'room_type', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        instance = self.instance
        if Room.objects.filter(name__iexact=value).exclude(pk=instance.pk if instance else None).exists():
            raise serializers.ValidationError("A room with this name already exists.")
        return value