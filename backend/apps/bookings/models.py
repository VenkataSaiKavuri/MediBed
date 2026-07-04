from django.conf import settings
from django.db import models

from apps.hospitals.models import BedType, Doctor, Hospital


class BookingStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    CONFIRMED = "confirmed", "Confirmed"
    REJECTED = "rejected", "Rejected"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No-show"
    ESCALATED = "escalated", "Escalated"  # emergency-only: forwarded to next hospital after SLA timeout


class Booking(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="bookings")
    doctor = models.ForeignKey(Doctor, null=True, blank=True, on_delete=models.SET_NULL, related_name="bookings")
    bed_type = models.CharField(max_length=20, choices=BedType.choices)

    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.REQUESTED)
    is_emergency = models.BooleanField(default=False)
    condition_category = models.CharField(max_length=100, blank=True)  # e.g. "cardiac", "trauma" — emergency only

    scheduled_time = models.DateTimeField(null=True, blank=True)  # non-emergency bookings only
    sla_deadline = models.DateTimeField(null=True, blank=True)     # hospital must respond by this time

    # --- Anti-fraud / deposit fields ---
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    deposit_paid = models.BooleanField(default=False)
    deposit_refunded = models.BooleanField(default=False)
    deposit_forfeited = models.BooleanField(default=False)  # true on no-show — the whole point of the deposit

    # Razorpay tracking — order created at booking time, payment_id captured after checkout,
    # refund_id captured if/when the deposit is returned
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_refund_id = models.CharField(max_length=100, blank=True)

    # --- Audit trail (critical for emergency fraud review, Day 25) ---
    device_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    patient_latitude = models.FloatField(null=True, blank=True)
    patient_longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_emergency", "status"]),
        ]

    def __str__(self):
        kind = "EMERGENCY" if self.is_emergency else "Scheduled"
        return f"[{kind}] {self.patient} -> {self.hospital} ({self.status})"


class BookingStatusLog(models.Model):
    """Immutable audit log of every status change — needed for disputes and fraud review."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
