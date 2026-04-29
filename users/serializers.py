from rest_framework import serializers
from .models import User

ROLE_MAP = {
    1: 'admin',
    2: 'reception',
    3: 'therapist',
}

class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    role_id          = serializers.IntegerField(write_only=True)

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password', 'role_id']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        if data['role_id'] not in ROLE_MAP:
            raise serializers.ValidationError("Invalid role_id. Use 1=Admin, 2=Receptionist, 3=Therapist")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already registered")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        role_id  = validated_data.pop('role_id')
        role     = ROLE_MAP[role_id]
        email    = validated_data['email']
        username = validated_data.get('username', email.split('@')[0])

        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password'],
            role=role
        )
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
            if not user.check_password(data['password']):
                raise serializers.ValidationError("Invalid credentials")
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'role',
            'phone', 'specialist_area', 'joining_date', 'years_of_experience',
        ]


class StaffUpdateSerializer(serializers.ModelSerializer):
    """
    Used by PUT /api/users/staff/<id>/
    All fields optional — only provided fields are updated.
    """
    role_id  = serializers.IntegerField(write_only=True, required=False)
    # Override username to skip AbstractUser's unique validator —
    # uniqueness is checked manually in validate_username instead.
    username             = serializers.CharField(required=False, allow_blank=True, max_length=150)
    years_of_experience  = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    profile_image        = serializers.ImageField(required=False, allow_null=True, allow_empty_file=False)

    class Meta:
        model  = User
        fields = [
            'username', 'email', 'role_id',
            'profile_image', 'phone', 'specialist_area', 'joining_date', 'years_of_experience',
        ]

    def validate_username(self, value):
        user = self.instance
        if User.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This name is already taken by another staff member.")
        return value

    def validate_role_id(self, value):
        if value not in ROLE_MAP:
            raise serializers.ValidationError("Invalid role_id. Use 1=Admin, 2=Receptionist, 3=Therapist")
        return value

    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Email already in use by another account.")
        return value

    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        if role_id is not None:
            instance.role = ROLE_MAP[role_id]
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# ─── Staff Schedule Serializers ───────────────────────────────────────────────

from .models import StaffWorkingHours, StaffBreakTime, StaffLeave


class WorkingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StaffWorkingHours
        fields = ['id', 'day', 'start_time', 'end_time']

    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("start_time must be before end_time.")
        return data


class BreakTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StaffBreakTime
        fields = ['id', 'start_time', 'end_time', 'label']

    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("start_time must be before end_time.")
        return data


class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StaffLeave
        fields = ['id', 'from_date', 'to_date', 'reason']

    def validate(self, data):
        if data.get('from_date') and data.get('to_date'):
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError("from_date must be on or before to_date.")
        return data