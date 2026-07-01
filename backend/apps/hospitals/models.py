from django.conf import settings
from django.db import models


class Hospital(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.FloatField()   # used for nearest-hospital emergency matching (Day 22)
    longitude = models.FloatField()
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)  # platform admin verifies real hospitals

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # drives the "last updated" staleness indicator (Day 27)

    def __str__(self):
        return self.name


class BedType(models.TextChoices):
    GENERAL = "general", "General"
    ICU = "icu", "ICU"
    VENTILATOR = "ventilator", "Ventilator"
    MATERNITY = "maternity", "Maternity"
    EMERGENCY = "emergency", "Emergency"


class BedInventory(models.Model):
    """
    Tracks bed counts per type, per hospital.
    total_count is set manually by hospital admin.
    available_count is auto-adjusted by booking lifecycle signals (Day 11) —
    never edited directly by the booking flow to avoid race conditions; use
    select_for_update() when decrementing/incrementing in a transaction.
    """
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="bed_inventory")
    bed_type = models.CharField(max_length=20, choices=BedType.choices)
    total_count = models.PositiveIntegerField(default=0)
    available_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("hospital", "bed_type")

    def __str__(self):
        return f"{self.hospital.name} - {self.bed_type}: {self.available_count}/{self.total_count}"


class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="doctors")
    specialty = models.CharField(max_length=100)
    is_on_duty = models.BooleanField(default=True)
    license_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.specialty})"


class EquipmentStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    IN_USE = "in_use", "In Use"
    MAINTENANCE = "maintenance", "Under Maintenance"


class Equipment(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="equipment")
    name = models.CharField(max_length=100)  # e.g. "Ventilator", "Dialysis Machine"
    total_count = models.PositiveIntegerField(default=0)
    available_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=EquipmentStatus.choices, default=EquipmentStatus.AVAILABLE)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hospital.name} - {self.name}"
