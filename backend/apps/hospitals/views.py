from rest_framework import permissions, viewsets, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsHospitalStaff

from .models import BedInventory, Doctor, Equipment, Hospital
from .serializers import (
    BedInventorySerializer,
    DoctorSerializer,
    EquipmentSerializer,
    HospitalDetailSerializer,
    HospitalListSerializer,
)


class HospitalListView(generics.ListAPIView):
    """Public-ish (any authenticated user) list of hospitals for patient search — Day 5 will add filters."""
    queryset = Hospital.objects.filter(is_verified=True)
    serializer_class = HospitalListSerializer
    permission_classes = [permissions.IsAuthenticated]


class HospitalDetailView(generics.RetrieveAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


class MyHospitalView(APIView):
    """Returns the logged-in hospital_admin/doctor's own hospital, fully nested with
    beds/doctors/equipment — this is what the Hospital Admin dashboard renders."""
    permission_classes = [permissions.IsAuthenticated, IsHospitalStaff]

    def get(self, request):
        if not request.user.hospital_id:
            raise NotFound("Your account isn't linked to a hospital yet. Contact platform admin.")
        hospital = Hospital.objects.get(id=request.user.hospital_id)
        return Response(HospitalDetailSerializer(hospital).data)


class HospitalScopedViewSetMixin:
    """
    Shared logic for any resource that belongs to a hospital (beds, doctors, equipment):
    - Only ever returns/affects rows belonging to the logged-in staff member's own hospital
    - Auto-attaches the hospital on create, so a malicious payload can't set hospital=<someone else's id>
    """
    permission_classes = [permissions.IsAuthenticated, IsHospitalStaff]

    def get_queryset(self):
        return self.queryset.model.objects.filter(hospital_id=self.request.user.hospital_id)

    def perform_create(self, serializer):
        serializer.save(hospital_id=self.request.user.hospital_id)


class BedInventoryViewSet(HospitalScopedViewSetMixin, viewsets.ModelViewSet):
    """
    Full CRUD for bed types at the admin's hospital.
    NOTE: available_count is read-only in the serializer — it's only ever changed by the
    booking lifecycle (Day 11), never edited directly here, to avoid mismatched counts.
    """
    queryset = BedInventory.objects.all()
    serializer_class = BedInventorySerializer


class DoctorViewSet(HospitalScopedViewSetMixin, viewsets.ModelViewSet):
    """CRUD for doctor roster at the admin's hospital."""
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class EquipmentViewSet(HospitalScopedViewSetMixin, viewsets.ModelViewSet):
    """CRUD for equipment at the admin's hospital."""
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
