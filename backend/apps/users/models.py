from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
        DOCTOR = "doctor", "Doctor"
        PLATFORM_ADMIN = "platform_admin", "Platform Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    phone_number = models.CharField(max_length=15, unique=True)
    phone_verified = models.BooleanField(default=False)

    # --- Anti-fraud fields ---
    reputation_score = models.IntegerField(default=100)  # decreases on no-shows/cancellations
    no_show_count = models.PositiveIntegerField(default=0)
    is_flagged = models.BooleanField(default=False)  # set True after repeated abuse; restricts instant booking
    id_document_verified = models.BooleanField(default=False)  # Aadhaar/passport check (Day 18)

    # For hospital_admin/doctor roles — which hospital they belong to
    hospital = models.ForeignKey(
        "hospitals.Hospital", null=True, blank=True, on_delete=models.SET_NULL, related_name="staff"
    )

    # Push notifications (Day 12) — set by the frontend after the browser/app grants notification
    # permission and Firebase issues a device token. Blank until then; notifications simply skip
    # push for users who haven't registered one yet (SMS still goes out regardless).
    fcm_token = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class OTPPurpose(models.TextChoices):
    SIGNUP = "signup", "Signup Verification"
    LOGIN = "login", "Login Verification"
    EMERGENCY_BOOKING = "emergency_booking", "Emergency Booking"


class OneTimePassword(models.Model):
    """
    Short-lived OTP codes for phone verification.
    A phone_number can have multiple OTP rows over time (old ones expire/get marked used);
    we never reuse or update a code in place, so there's always an audit trail.
    """
    phone_number = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=OTPPurpose.choices, default=OTPPurpose.SIGNUP)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)  # brute-force guard, max 5 tries per code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"OTP for {self.phone_number} ({self.purpose})"


class DocumentType(models.TextChoices):
    AADHAAR = "aadhaar", "Aadhaar Card"
    PASSPORT = "passport", "Passport"


class NameMatchResult(models.TextChoices):
    EXACT_MATCH = "exact_match", "Exact Match"
    CLOSE_MATCH = "close_match", "Close Match"
    MISMATCH = "mismatch", "Mismatch — Needs Review"


class IdentityDocument(models.Model):
    """
    A patient's uploaded ID document, required once before non-emergency booking (Day 18).
    The file is ENCRYPTED before being written to disk (see apps/users/encryption.py) —
    never accessible via Django's normal media URL serving, only through the
    access-controlled download view.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="identity_documents")
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    encrypted_file = models.FileField(upload_to="identity_documents/%Y/%m/")
    name_on_document = models.CharField(max_length=255)  # self-reported by the patient at upload time
    name_match_result = models.CharField(max_length=20, choices=NameMatchResult.choices)
    name_match_score = models.FloatField()  # 0.0-1.0 similarity ratio, for admin review context

    # Manual review (platform admin, Day 19's dashboard) — a mismatch doesn't block booking
    # today (soft signal, matching Day 17's philosophy), but a human can review and override.
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_documents"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} for {self.user} ({self.name_match_result})"
