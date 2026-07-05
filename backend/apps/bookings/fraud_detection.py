"""
Lightweight fraud signals evaluated at booking-creation time. Split into two categories:

HARD RULES (raise and block creation entirely):
  - Duplicate active booking: same patient, same hospital, same bed type, already has a
    requested/confirmed booking. This is what actually stops "book the same bed 5 times in
    a row" spam that a plain rate limit doesn't catch — a patient could stay under 10/hour
    while still creating 5 duplicate requests for one bed.

SOFT SIGNALS (flag for platform admin review, Day 19's dashboard — never auto-block):
  - Device/IP shared across an unusual number of distinct patient accounts recently. A
    shared family phone or a hospital's public kiosk can trigger this legitimately, so it's
    a flag, not a rejection.
  - Rapid-fire booking creation from the same device — several bookings within a very short
    window looks scripted, but could also just be someone quickly booking beds for multiple
    family members during a real emergency, hence: flag, don't block.
"""
from datetime import timedelta

from django.utils import timezone

from .models import Booking, BookingStatus

DEVICE_SHARING_ACCOUNT_THRESHOLD = 3   # distinct patient accounts using one device_id/IP
DEVICE_SHARING_WINDOW_HOURS = 24
RAPID_FIRE_COUNT_THRESHOLD = 3         # bookings from the same device...
RAPID_FIRE_WINDOW_MINUTES = 5          # ...within this many minutes

ACTIVE_STATUSES = {BookingStatus.REQUESTED, BookingStatus.CONFIRMED, BookingStatus.ESCALATED}


def has_duplicate_active_booking(patient, hospital, bed_type) -> bool:
    """HARD RULE. True if this patient already has an unresolved booking for the same
    hospital + bed type — used to block creation of a new one outright."""
    return Booking.objects.filter(
        patient=patient,
        hospital=hospital,
        bed_type=bed_type,
        status__in=ACTIVE_STATUSES,
    ).exists()


def detect_device_ip_sharing(device_id: str, ip_address: str, patient) -> list[str]:
    """SOFT SIGNAL. Flags if this device_id or IP has been used by an unusual number of
    DIFFERENT patient accounts recently — a pattern consistent with one person spinning up
    multiple fake accounts to get around per-account limits."""
    reasons = []
    since = timezone.now() - timedelta(hours=DEVICE_SHARING_WINDOW_HOURS)

    if device_id:
        distinct_patients = (
            Booking.objects.filter(device_id=device_id, created_at__gte=since)
            .exclude(patient=patient)
            .values_list("patient_id", flat=True)
            .distinct()
        )
        if len(distinct_patients) >= DEVICE_SHARING_ACCOUNT_THRESHOLD - 1:  # -1: +this patient = threshold
            reasons.append(f"device_id used by {len(distinct_patients) + 1} distinct accounts in {DEVICE_SHARING_WINDOW_HOURS}h")

    if ip_address:
        distinct_patients = (
            Booking.objects.filter(ip_address=ip_address, created_at__gte=since)
            .exclude(patient=patient)
            .values_list("patient_id", flat=True)
            .distinct()
        )
        if len(distinct_patients) >= DEVICE_SHARING_ACCOUNT_THRESHOLD - 1:
            reasons.append(f"IP address used by {len(distinct_patients) + 1} distinct accounts in {DEVICE_SHARING_WINDOW_HOURS}h")

    return reasons


def detect_rapid_fire(device_id: str, patient) -> list[str]:
    """SOFT SIGNAL. Flags if this device has created several bookings in a very short window."""
    if not device_id:
        return []
    since = timezone.now() - timedelta(minutes=RAPID_FIRE_WINDOW_MINUTES)
    recent_count = Booking.objects.filter(device_id=device_id, created_at__gte=since).count()
    if recent_count >= RAPID_FIRE_COUNT_THRESHOLD:
        return [f"{recent_count} bookings from this device in {RAPID_FIRE_WINDOW_MINUTES} minutes"]
    return []


def evaluate_soft_fraud_signals(booking: Booking) -> list[str]:
    """Runs all soft-signal checks and returns the combined list of reasons (empty if clean).
    Caller is responsible for saving is_suspicious/fraud_flags onto the booking."""
    reasons = []
    reasons += detect_device_ip_sharing(booking.device_id, booking.ip_address, booking.patient)
    reasons += detect_rapid_fire(booking.device_id, booking.patient)
    return reasons
