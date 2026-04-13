from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)  # 👈 new

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password', 'role']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # 👈 remove before saving
        user = User.objects.create_user(
            username=validated_data.get('username', validated_data['email'].split('@')[0]),
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'client')
        )
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
            auth_user = authenticate(
                username=user.username,
                password=data['password']
            )
            if not auth_user:
                raise serializers.ValidationError("Invalid credentials")
            return auth_user
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']