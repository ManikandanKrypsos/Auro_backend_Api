from rest_framework import serializers
from .models import User

ROLE_MAP = {
    1: 'admin',
    2: 'reception',
    3: 'therapist',
    4: 'client',
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
            raise serializers.ValidationError("Invalid role_id. Use 1=Admin, 2=Receptionist, 3=Therapist, 4=Client")
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
        fields = ['id', 'username', 'email', 'role']