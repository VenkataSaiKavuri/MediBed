from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import IdentityDocument, NameMatchResult, OTPPurpose

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

    def validate_phone_number(self, value):
        # Day 29: basic E.164-ish format check — was previously unvalidated (any string up
        # to 15 chars was accepted, including garbage that would silently break SMS delivery
        # later). Doesn't verify the number is real/reachable, just that it's shaped correctly.
        import re
        if not re.match(r"^\+?[1-9]\d{7,14}$", value):
            raise serializers.ValidationError(
                "Enter a valid phone number with country code, e.g. +919876543210."
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


class IdentityDocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityDocument
        fields = ["id", "document_type", "encrypted_file", "name_on_document"]
        extra_kwargs = {"encrypted_file": {"write_only": True}}

    def create(self, validated_data):
        from .encryption import encrypt_bytes
        from .name_matching import compute_name_match
        from django.core.files.base import ContentFile

        request = self.context["request"]
        uploaded_file = validated_data.pop("encrypted_file")
        name_on_document = validated_data["name_on_document"]

        raw_bytes = uploaded_file.read()
        encrypted_bytes = encrypt_bytes(raw_bytes)

        account_name = request.user.get_full_name() or request.user.username
        match_result, match_score = compute_name_match(account_name, name_on_document)

        doc = IdentityDocument.objects.create(
            user=request.user,
            document_type=validated_data["document_type"],
            name_on_document=name_on_document,
            name_match_result=match_result,
            name_match_score=match_score,
        )
        doc.encrypted_file.save(
            f"{request.user.id}_{uploaded_file.name}",
            ContentFile(encrypted_bytes),
            save=True,
        )

        # Auto-verify on a confident match; anything less gets left for manual review
        # (Day 19's platform admin dashboard) rather than silently trusting a shaky match.
        if match_result == NameMatchResult.EXACT_MATCH:
            request.user.id_document_verified = True
            request.user.save(update_fields=["id_document_verified"])

        return doc


class IdentityDocumentStatusSerializer(serializers.ModelSerializer):
    """Read-only status view for the patient — never exposes the encrypted file itself."""
    class Meta:
        model = IdentityDocument
        fields = ["id", "document_type", "name_on_document", "name_match_result", "uploaded_at"]
        read_only_fields = fields
