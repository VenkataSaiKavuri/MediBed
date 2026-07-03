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
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Doctor
        fields = ["id", "name", "user_id", "specialty", "is_on_duty", "license_number"]

    def validate_user_id(self, value):
        from apps.users.models import User
        try:
            user = User.objects.get(id=value, role="doctor")
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No doctor account found with this user ID. The account must already exist "
                "with role='doctor' (create it in Django admin first, then link it here)."
            )
        return value

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")
        return Doctor.objects.create(user_id=user_id, **validated_data)


class HospitalListSerializer(serializers.ModelSerializer):
    """Lightweight — used for the patient-facing search list. Includes just enough
    bed/specialty info to let a patient judge relevance without an extra API call per hospital."""
    available_beds = serializers.SerializerMethodField()
    specialties = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = [
            "id", "name", "city", "address", "latitude", "longitude", "phone_number",
            "is_verified", "available_beds", "specialties",
        ]

    def get_available_beds(self, obj):
        return {
            bed.bed_type: bed.available_count
            for bed in obj.bed_inventory.all()
        }

    def get_specialties(self, obj):
        return sorted({doc.specialty for doc in obj.doctors.all() if doc.is_on_duty})


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
