from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.hospitals.models import BedType

from .models import Booking, BookingStatus, BookingStatusLog
from .payments import create_order, get_deposit_amount
from .fraud_detection import evaluate_soft_fraud_signals, has_duplicate_active_booking

# Matches the original plan's Day 10 spec: 2 hours for hospitals to respond to a
# non-emergency booking request. Emergency bookings (Day 23) get a much shorter SLA.
SCHEDULED_BOOKING_SLA_HOURS = 2

# Emergency requests need a hospital response fast — Day 23 will build the actual alert
# system and Day 24 the auto-escalation to the next hospital once this expires. For now,
# the deadline is just set here so those later days have something to act on.
EMERGENCY_BOOKING_SLA_MINUTES = 15


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
            "scheduled_time", "sla_deadline", "confirmed_at", "deposit_amount", "deposit_paid",
            "deposit_refunded", "deposit_forfeited", "razorpay_order_id", "razorpay_payment_id",
            "created_at", "updated_at", "status_logs",
        ]
        read_only_fields = [
            "id", "status", "sla_deadline", "confirmed_at", "deposit_amount", "deposit_paid",
            "deposit_refunded", "deposit_forfeited", "razorpay_order_id", "razorpay_payment_id",
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
        # Flagged users (repeat no-shows/late-cancellers) lose instant-booking privileges —
        # this is the actual enforcement point for Day 16's reputation system. Without this
        # check, flagging a user would just be a label with no real consequence.
        request = self.context["request"]
        if request.user.is_flagged:
            raise serializers.ValidationError(
                "Your account has restricted booking privileges due to repeated no-shows or "
                "late cancellations. Please call the hospital directly, or contact support to "
                "restore instant booking."
            )

        # Day 18: at least one ID document must be on file before a non-emergency booking
        # can be created. Note this only requires an UPLOAD to exist — it does not require
        # id_document_verified=True (an exact name match), since that would block genuine
        # patients over a shaky string-similarity check with no human review yet available.
        # A mismatch is still recorded and surfaced for platform admin review (Day 19),
        # matching the same soft-signal philosophy as Day 17.
        from apps.users.models import IdentityDocument
        if not IdentityDocument.objects.filter(user=request.user).exists():
            raise serializers.ValidationError(
                "Please upload an ID document (Aadhaar or passport) before booking. "
                "This is a one-time step to help prevent fraudulent bookings."
            )

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

        # HARD RULE: block duplicate active bookings for the same hospital + bed type — this
        # is what actually stops "spam the same bed 5 times" abuse that a plain hourly rate
        # limit alone doesn't catch.
        bed_type = attrs.get("bed_type")
        if bed_type and hospital and has_duplicate_active_booking(request.user, hospital, bed_type):
            raise serializers.ValidationError(
                "You already have an active request for this bed type at this hospital. "
                "Cancel it first if you'd like to submit a new one."
            )
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

        # Soft fraud signals — never block creation over these, just flag for platform admin
        # review (Day 19's dashboard). A shared device/IP or a burst of bookings can be
        # completely legitimate (family member booking for several relatives during a real
        # emergency), so a human should judge these, not the system.
        fraud_reasons = evaluate_soft_fraud_signals(booking)
        if fraud_reasons:
            booking.is_suspicious = True
            booking.fraud_flags = fraud_reasons
            booking.save(update_fields=["razorpay_order_id", "is_suspicious", "fraud_flags"])
        else:
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


class CreateEmergencyBookingSerializer(serializers.ModelSerializer):
    """
    Emergency booking creation — deliberately minimal and fast. Unlike CreateBookingSerializer,
    this SKIPS:
      - ID document requirement (Day 18) — no time for that when it's urgent
      - Flagged-user block (Day 16) — a fraud flag shouldn't be able to delay emergency care;
        the platform accepts higher fraud risk here in exchange for speed, by design
      - Duplicate-active-booking check (Day 17) — someone in crisis might reasonably need to
        try multiple hospitals at once if the first doesn't respond fast enough
      - Deposit collection (Day 13) — payment friction has no place in an emergency flow

    Everything is still logged (device_id, IP, geolocation) for post-hoc fraud review, matching
    the original plan's explicit trade-off: speed now, audit later, never the reverse.
    """
    class Meta:
        model = Booking
        fields = [
            "id", "hospital", "bed_type", "condition_category",
            "patient_latitude", "patient_longitude", "sla_deadline",
        ]
        read_only_fields = ["id", "sla_deadline"]

    def validate_bed_type(self, value):
        if value not in BedType.values:
            raise serializers.ValidationError("Invalid bed type.")
        return value

    def create(self, validated_data):
        from apps.core.notifications import notify_booking_status_change

        request = self.context["request"]
        booking = Booking.objects.create(
            patient=request.user,
            status=BookingStatus.REQUESTED,
            is_emergency=True,
            device_id=request.headers.get("X-Device-Id", ""),
            ip_address=request.META.get("REMOTE_ADDR"),
            sla_deadline=timezone.now() + timedelta(minutes=EMERGENCY_BOOKING_SLA_MINUTES),
            deposit_amount=0,  # no deposit for emergency bookings — see class docstring
            **validated_data,
        )
        try:
            notify_booking_status_change(booking)
        except Exception as e:  # noqa: BLE001 — never let a notification failure delay an emergency booking
            print(f"[notification error] Failed to notify emergency booking {booking.id}: {e}")
        return booking
