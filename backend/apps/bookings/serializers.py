from rest_framework import serializers

from apps.hospitals.models import BedType

from .models import Booking, BookingStatus, BookingStatusLog


class BookingStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.get_full_name", read_only=True, default="System")

    class Meta:
        model = BookingStatusLog
        fields = ["id", "from_status", "to_status", "changed_by_name", "note", "timestamp"]


class BookingSerializer(serializers.ModelSerializer):
    """Full read representation — used for detail views and hospital admin's booking list."""
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    patient_phone = serializers.CharField(source="patient.phone_number", read_only=True)
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.user.get_full_name", read_only=True, default=None)
    status_logs = BookingStatusLogSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "patient", "patient_name", "patient_phone", "hospital", "hospital_name",
            "doctor", "doctor_name", "bed_type", "status", "is_emergency", "condition_category",
            "scheduled_time", "sla_deadline", "deposit_amount", "deposit_paid", "deposit_refunded",
            "created_at", "updated_at", "status_logs",
        ]
        read_only_fields = [
            "id", "status", "sla_deadline", "deposit_amount", "deposit_paid", "deposit_refunded",
            "created_at", "updated_at", "status_logs",
        ]


class CreateBookingSerializer(serializers.ModelSerializer):
    """Non-emergency booking creation — patient picks hospital, bed type, doctor (optional), time."""

    class Meta:
        model = Booking
        fields = ["id", "hospital", "doctor", "bed_type", "scheduled_time", "condition_category"]
        read_only_fields = ["id"]

    def validate_bed_type(self, value):
        if value not in BedType.values:
            raise serializers.ValidationError("Invalid bed type.")
        return value

    def validate(self, attrs):
        # A doctor, if specified, must belong to the chosen hospital — prevents cross-hospital mismatches
        doctor = attrs.get("doctor")
        hospital = attrs.get("hospital")
        if doctor and hospital and doctor.hospital_id != hospital.id:
            raise serializers.ValidationError("Selected doctor does not belong to the selected hospital.")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return Booking.objects.create(
            patient=request.user,
            status=BookingStatus.REQUESTED,
            is_emergency=False,
            device_id=request.headers.get("X-Device-Id", ""),
            ip_address=request.META.get("REMOTE_ADDR"),
            **validated_data,
        )


class TransitionBookingSerializer(serializers.Serializer):
    """Used by hospital admin (confirm/reject) and patient (cancel) to move a booking's status."""
    status = serializers.ChoiceField(choices=BookingStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)
