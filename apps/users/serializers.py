"""DRF Serializers — Users"""
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone", "full_name", "business_name", "is_verified", "date_joined"]
        read_only_fields = ["id", "is_verified", "date_joined"]


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=120)
    business_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, data):
        if not data.get("email") and not data.get("phone"):
            raise serializers.ValidationError("Either email or phone is required.")
        return data
