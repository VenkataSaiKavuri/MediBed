from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.hospitals.models import BedType

from .models import Booking, BookingStatus, BookingStatusLog
from .payments import create_order, get_deposit_amount

# Matches the original plan's Day 10 spec: 2 hours for hospitals to respond to a
# non-emergency booking request. Emergency bookings (Day 23) get a much shorter SLA.
SCHEDULED_BOOKING_SLA_HOURS = 2


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
            "deposit_forfeited", "razorpay_order_id", "razorpay_payment_id",
            "created_at", "updated_at", "status_logs",
        ]
        read_only_fields = [
            "id", "status", "sla_deadline", "deposit_amount", "deposit_paid", "deposit_refunded",
            "deposit_forfeited", "razorpay_order_id", "razorpay_payment_id",
            "created_at", "updated_at", "status_logs",
        ]


class CreateBookingSerializer(serializers.ModelSerializer):
    """Non-emergency booking creation — patient picks hospital, bed type, doctor (optional), time."""
    razorpay_key_id = serializers.SerializerMethodField()
    is_stub_payment = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id", "hospital", "doctor", "bed_type", "scheduled_time", "condition_category",
            "sla_deadline", "deposit_amount", "razorpay_order_id", "razorpay_key_id", "is_stub_payment",
        ]
        read_only_fields = ["id", "sla_deadline", "deposit_amount", "razorpay_order_id"]

    def get_razorpay_key_id(self, obj):
        from django.conf import settings
        return settings.RAZORPAY_KEY_ID or None

    def get_is_stub_payment(self, obj):
        return obj.razorpay_order_id.startswith("order_dev_")

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
        # A patient shouldn't be able to request a doctor who's currently off-duty — the
        # frontend already filters these out of the dropdown, but the API must enforce it
        # too, since anyone could bypass the UI and post a doctor ID directly.
        if doctor and not doctor.is_on_duty:
            raise serializers.ValidationError("Selected doctor is not currently on duty.")
        return attrs

    def create(self, validated_data):
        from apps.core.notifications import notify_booking_status_change

        request = self.context["request"]
        bed_type = validated_data["bed_type"]
        deposit_amount = get_deposit_amount(bed_type)

        booking = Booking.objects.create(
            patient=request.user,
            status=BookingStatus.REQUESTED,
            is_emergency=False,
            device_id=request.headers.get("X-Device-Id", ""),
            ip_address=request.META.get("REMOTE_ADDR"),
            sla_deadline=timezone.now() + timedelta(hours=SCHEDULED_BOOKING_SLA_HOURS),
            deposit_amount=deposit_amount,
            **validated_data,
        )

        order = create_order(deposit_amount, receipt=f"booking-{booking.id}")
        booking.razorpay_order_id = order["id"]
        booking.save(update_fields=["razorpay_order_id"])

        try:
            notify_booking_status_change(booking)
        except Exception as e:  # noqa: BLE001 — never let a notification failure break booking creation
            print(f"[notification error] Failed to notify new booking {booking.id}: {e}")
        return booking


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField(required=False, allow_blank=True)


class TransitionBookingSerializer(serializers.Serializer):
    """Used by hospital admin (confirm/reject) and patient (cancel) to move a booking's status."""
    status = serializers.ChoiceField(choices=BookingStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)
