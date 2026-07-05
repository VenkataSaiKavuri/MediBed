from rest_framework import serializers

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingSerializer
from apps.users.models import IdentityDocument
from apps.users.serializers import UserProfileSerializer


class FlaggedUserSerializer(UserProfileSerializer):
    """UserProfileSerializer already includes reputation_score, no_show_count, is_flagged —
    reused as-is for the fraud dashboard's flagged-user list."""
    pass


class SuspiciousBookingSerializer(BookingSerializer):
    """Adds the fields platform admin needs to actually judge a flagged booking that the
    normal patient/hospital-facing BookingSerializer deliberately omits."""
    fraud_flags = serializers.JSONField(read_only=True)
    device_id = serializers.CharField(read_only=True)
    ip_address = serializers.CharField(read_only=True)

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ["fraud_flags", "device_id", "ip_address"]


class IdentityDocumentReviewSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="user.get_full_name", read_only=True)
    patient_phone = serializers.CharField(source="user.phone_number", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = IdentityDocument
        fields = [
            "id", "patient_name", "patient_phone", "document_type", "name_on_document",
            "name_match_result", "name_match_score", "reviewed", "reviewed_at", "uploaded_at",
            "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        return f"/api/auth/identity-documents/{obj.id}/download/"


class ReviewActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
