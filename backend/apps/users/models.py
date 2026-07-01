from django.contrib.auth.models import AbstractUser
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

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
