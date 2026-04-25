from rest_framework import serializers
from .models import ClinicHours, PlannedClosure


class ClinicHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ClinicHours
        fields = ['id', 'day', 'is_open', 'open_time', 'close_time']

    def validate(self, data):
        is_open    = data.get('is_open', self.instance.is_open if self.instance else False)
        open_time  = data.get('open_time',  self.instance.open_time  if self.instance else None)
        close_time = data.get('close_time', self.instance.close_time if self.instance else None)

        if is_open:
            if not open_time:
                raise serializers.ValidationError("open_time is required when is_open is true.")
            if not close_time:
                raise serializers.ValidationError("close_time is required when is_open is true.")
            if open_time >= close_time:
                raise serializers.ValidationError("open_time must be before close_time.")
        return data


class BulkClinicHoursSerializer(serializers.Serializer):
    """
    Accepts a list of all 7 days in one request.
    [
        { "day": "Mon", "is_open": true,  "open_time": "09:00", "close_time": "18:00" },
        { "day": "Sat", "is_open": false }
    ]
    """
    day        = serializers.ChoiceField(choices=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    is_open    = serializers.BooleanField(default=False)
    open_time  = serializers.TimeField(required=False, allow_null=True)
    close_time = serializers.TimeField(required=False, allow_null=True)

    def validate(self, data):
        if data.get('is_open'):
            if not data.get('open_time'):
                raise serializers.ValidationError("open_time is required when is_open is true.")
            if not data.get('close_time'):
                raise serializers.ValidationError("close_time is required when is_open is true.")
            if data['open_time'] >= data['close_time']:
                raise serializers.ValidationError("open_time must be before close_time.")
        return data


class PlannedClosureSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PlannedClosure
        fields = ['id', 'from_date', 'to_date', 'reason', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, data):
        from_date = data.get('from_date', self.instance.from_date if self.instance else None)
        to_date   = data.get('to_date',   self.instance.to_date   if self.instance else None)
        if from_date and to_date and from_date > to_date:
            raise serializers.ValidationError("from_date must be on or before to_date.")
        return data