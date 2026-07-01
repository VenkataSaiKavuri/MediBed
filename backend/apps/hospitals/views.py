from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsHospitalStaff

from .models import BedInventory, Equipment, Hospital
from .serializers import (
    BedInventorySerializer,
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


class UpdateBedInventoryView(generics.UpdateAPIView):
    """Hospital admin edits total_count for a bed type. available_count is never touched here —
    it's only adjusted by the booking lifecycle (Day 11)."""
    queryset = BedInventory.objects.all()
    serializer_class = BedInventorySerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalStaff]

    def get_queryset(self):
        # Scope to the admin's own hospital so they can't edit another hospital's beds
        return BedInventory.objects.filter(hospital_id=self.request.user.hospital_id)


class UpdateEquipmentView(generics.UpdateAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalStaff]

    def get_queryset(self):
        return Equipment.objects.filter(hospital_id=self.request.user.hospital_id)
