from django.db.models import Q
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
    """
    Patient-facing hospital search.
    Supports query params (all optional, combinable):
      ?city=Guntur
      ?bed_type=icu          -> only hospitals with at least 1 available bed of this type
      ?specialty=cardiology  -> only hospitals with an on-duty doctor of this specialty (case-insensitive contains)
      ?search=apollo         -> name/city contains
    """
    serializer_class = HospitalListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Hospital.objects.filter(is_verified=True).prefetch_related("bed_inventory", "doctors")

        city = self.request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(city__icontains=search))

        bed_type = self.request.query_params.get("bed_type")
        if bed_type:
            qs = qs.filter(bed_inventory__bed_type=bed_type, bed_inventory__available_count__gt=0)

        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(doctors__specialty__icontains=specialty, doctors__is_on_duty=True)

        return qs.distinct()


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
