from rest_framework import serializers

from .models import BedInventory, Doctor, Equipment, Hospital


class BedInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BedInventory
        fields = ["id", "bed_type", "total_count", "available_count", "updated_at"]
        read_only_fields = ["available_count", "updated_at"]  # available_count only changes via booking lifecycle


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ["id", "name", "total_count", "available_count", "status", "updated_at"]


class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Doctor
        fields = ["id", "name", "specialty", "is_on_duty", "license_number"]


class HospitalListSerializer(serializers.ModelSerializer):
    """Lightweight — used for the patient-facing search list."""
    class Meta:
        model = Hospital
        fields = ["id", "name", "city", "address", "latitude", "longitude", "phone_number", "is_verified"]


class HospitalDetailSerializer(serializers.ModelSerializer):
    """Full nested detail — used for hospital admin's own dashboard and patient hospital-detail view."""
    bed_inventory = BedInventorySerializer(many=True, read_only=True)
    equipment = EquipmentSerializer(many=True, read_only=True)
    doctors = DoctorSerializer(many=True, read_only=True)

    class Meta:
        model = Hospital
        fields = [
            "id", "name", "city", "address", "latitude", "longitude", "phone_number",
            "is_verified", "updated_at", "bed_inventory", "equipment", "doctors",
        ]
