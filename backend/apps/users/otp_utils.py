import hashlib
import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import OneTimePassword, OTPPurpose

OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 5
MAX_VERIFY_ATTEMPTS = 5


def _hash_code(code: str) -> str:
    """
    Day 29 security pass: OTP codes are hashed before storage, the same principle as
    password hashing — a database leak (backup exposure, SQL injection, insider access)
    should never hand out valid, unexpired OTP codes in plaintext. Uses SHA-256 salted
    with SECRET_KEY; a full password-hasher (PBKDF2/bcrypt) would be overkill here since
    OTP codes are short-lived (5 min) and rate-limited (5 attempts), unlike a password
    an attacker could brute-force offline at leisure.
    """
    return hashlib.sha256(f"{code}{settings.SECRET_KEY}".encode()).hexdigest()


def generate_and_send_otp(phone_number: str, purpose: str = OTPPurpose.SIGNUP) -> OneTimePassword:
    """Creates a new OTP row and 'sends' it. Swap send_sms() for a real provider before production."""
    code = "".join(random.choices("0123456789", k=OTP_LENGTH))
    otp = OneTimePassword.objects.create(
        phone_number=phone_number,
        code=_hash_code(code),  # only the hash is ever stored
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES),
    )
    send_sms(phone_number, f"Your MedBeds verification code is {code}. Valid for {OTP_VALIDITY_MINUTES} minutes.")
    return otp


def verify_otp(phone_number: str, code: str, purpose: str = OTPPurpose.SIGNUP) -> tuple[bool, str]:
    """Returns (success, message). Marks the OTP used on success; increments attempts on failure."""
    otp = (
        OneTimePassword.objects.filter(phone_number=phone_number, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp:
        return False, "No pending OTP for this number. Request a new one."

    if timezone.now() > otp.expires_at:
        return False, "OTP expired. Request a new one."

    if otp.attempts >= MAX_VERIFY_ATTEMPTS:
        return False, "Too many incorrect attempts. Request a new OTP."

    if otp.code != _hash_code(code):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        return False, "Incorrect OTP."

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    return True, "OTP verified."


def send_sms(phone_number: str, message: str) -> None:
    """
    STUB — replace with a real SMS provider (Twilio, MSG91, etc.) before production.
    For now this just logs to console so you can see OTP codes during local development.
    """
    if settings.DEBUG:
        print(f"[SMS STUB] To: {phone_number} | Message: {message}")
    else:
        # TODO: integrate real provider, e.g.:
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
        # client.messages.create(to=phone_number, from_=settings.TWILIO_FROM_NUMBER, body=message)
        raise NotImplementedError("Configure a real SMS provider in send_sms() before going to production.")
