"""
Centralized notification content and dispatch. Every booking status change should
result in exactly one notification attempt via notify_booking_status_change() —
call it from the state machine (services.py), never scatter ad-hoc send_sms() calls
across views.

SMS uses the same stub as OTP (apps/users/otp_utils.send_sms) — logs to console in DEBUG,
raises NotImplementedError in production until a real provider is wired in.

Push uses a new stub here — swap send_push() for real Firebase Cloud Messaging calls
before production (see the TODO inside).
"""
from django.conf import settings

# {status: (sms_template, push_title, push_body_template)}
# All templates receive: patient_name, hospital_name, bed_type
NOTIFICATION_TEMPLATES = {
    "requested": (
        "MedBeds: Your {bed_type} bed request at {hospital_name} has been sent. "
        "We'll notify you once the hospital responds.",
        "Booking request sent",
        "Your {bed_type} bed request at {hospital_name} is awaiting confirmation.",
    ),
    "confirmed": (
        "MedBeds: Good news! Your {bed_type} bed at {hospital_name} is CONFIRMED. Please proceed to the hospital.",
        "Booking confirmed ✅",
        "Your {bed_type} bed at {hospital_name} has been confirmed.",
    ),
    "rejected": (
        "MedBeds: Your {bed_type} bed request at {hospital_name} was declined. Please search for another hospital.",
        "Booking declined",
        "{hospital_name} couldn't accommodate your {bed_type} bed request.",
    ),
    "completed": (
        "MedBeds: Your stay at {hospital_name} has been marked complete. Thank you for using MedBeds.",
        "Stay completed",
        "Your booking at {hospital_name} is now complete.",
    ),
    "cancelled": (
        "MedBeds: Your {bed_type} bed booking at {hospital_name} has been cancelled.",
        "Booking cancelled",
        "Your booking at {hospital_name} was cancelled.",
    ),
    "no_show": (
        "MedBeds: You were marked as a no-show for your {bed_type} bed booking at {hospital_name}. "
        "Repeated no-shows may restrict future instant bookings.",
        "Marked as no-show",
        "You missed your confirmed booking at {hospital_name}.",
    ),
    "escalated": (
        "MedBeds: {hospital_name} didn't respond in time — we're finding you another hospital now.",
        "Finding another hospital",
        "Your emergency request is being escalated to another hospital.",
    ),
}


def _fill(template: str, booking) -> str:
    return template.format(
        patient_name=booking.patient.get_full_name() or booking.patient.username,
        hospital_name=booking.hospital.name,
        bed_type=booking.bed_type,
    )


def send_push(fcm_token: str, title: str, body: str) -> None:
    """
    STUB — swap for real Firebase Cloud Messaging before production. Example real implementation:

        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=fcm_token,
        )
        messaging.send(message)

    For now, just logs so you can see push notifications "fire" during local development.
    """
    if not fcm_token:
        return
    if settings.DEBUG:
        print(f"[PUSH STUB] To token {fcm_token[:12]}... | {title}: {body}")
    else:
        raise NotImplementedError("Configure Firebase Cloud Messaging in send_push() before production.")


def notify_booking_status_change(booking) -> None:
    """Call this once, right after a booking's status changes. Sends both SMS and push (if the
    patient has a registered device token)."""
    from apps.users.otp_utils import send_sms  # local import avoids a circular import at module load time

    templates = NOTIFICATION_TEMPLATES.get(booking.status)
    if not templates:
        return  # No template defined for this status (shouldn't happen, but don't crash a booking action over it)

    sms_template, push_title, push_body_template = templates

    try:
        send_sms(booking.patient.phone_number, _fill(sms_template, booking))
    except NotImplementedError:
        pass  # Production without a real SMS provider configured yet — don't crash the booking flow over it

    fcm_token = getattr(booking.patient, "fcm_token", "")
    if fcm_token:
        try:
            send_push(fcm_token, push_title, _fill(push_body_template, booking))
        except NotImplementedError:
            pass


def notify_hospital_of_emergency(booking) -> None:
    """
    Day 23: instant alert straight to the hospital when an emergency request lands — this is
    hospital-facing, not patient-facing, so it doesn't use the per-status templates above.
    Sent to the hospital's registered phone number (Hospital.phone_number). In production this
    should go to whichever number/system a hospital actually monitors in real time — a shared
    front-desk phone, a dedicated on-call line, etc. — configurable per hospital in a future
    iteration if a single number per hospital proves too coarse.
    """
    from apps.users.otp_utils import send_sms

    message = (
        f"URGENT MedBeds Alert: Emergency {booking.bed_type} bed request "
        f"({booking.condition_category or 'unspecified condition'}) from "
        f"{booking.patient.get_full_name() or booking.patient.username} "
        f"({booking.patient.phone_number}). Respond within 15 minutes in the MedBeds dashboard."
    )
    try:
        send_sms(booking.hospital.phone_number, message)
    except NotImplementedError:
        pass  # Production without a real SMS provider configured yet — don't crash booking creation over it
