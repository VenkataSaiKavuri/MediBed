from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import OTPPurpose

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "phone_number", "password", "role", "first_name", "last_name"]
        extra_kwargs = {
            "role": {"required": False},  # defaults to 'patient'; hospital_admin/doctor accounts
                                            # should be created via Django admin or an invite flow,
                                            # not public self-signup — prevents fake hospital accounts.
        }

    def validate_role(self, value):
        if value in ("hospital_admin", "doctor", "platform_admin"):
            raise serializers.ValidationError(
                "This role can't be self-registered. Contact platform admin for staff accounts."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    purpose = serializers.ChoiceField(choices=OTPPurpose.choices, default=OTPPurpose.SIGNUP)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=OTPPurpose.choices, default=OTPPurpose.SIGNUP)


class UserProfileSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source="hospital.name", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "phone_number", "phone_verified",
            "role", "first_name", "last_name", "hospital", "hospital_name",
            "reputation_score", "no_show_count", "is_flagged",
        ]
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role + phone_verified to the JWT payload so the frontend can route by role immediately."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["phone_verified"] = user.phone_verified
        token["full_name"] = user.get_full_name() or user.username
        return token
