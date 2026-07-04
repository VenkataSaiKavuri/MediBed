from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.permissions import IsHospitalStaff, IsPatient

from .models import Booking, BookingStatus
from .serializers import BookingSerializer, CreateBookingSerializer, TransitionBookingSerializer
from .services import InvalidTransitionError, NoBedAvailableError, transition_booking

# Which target statuses each role is allowed to request — enforced here, ON TOP of the
# state-machine's own transition rules in services.py. A role check alone isn't enough
# (e.g. it shouldn't matter that COMPLETED is a valid state from CONFIRMED if a *patient*
# is the one asking for it — only hospital staff mark bookings completed).
PATIENT_ALLOWED_TARGETS = {BookingStatus.CANCELLED}
HOSPITAL_STAFF_ALLOWED_TARGETS = {
    BookingStatus.CONFIRMED, BookingStatus.REJECTED, BookingStatus.COMPLETED, BookingStatus.NO_SHOW,
}


class CreateBookingView(generics.CreateAPIView):
    """Patient creates a non-emergency booking request."""
    serializer_class = CreateBookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "booking_create"  # 10/hour, set in settings.py — anti-spam guard

    def get_serializer_context(self):
        return {"request": self.request}


class MyBookingsView(generics.ListAPIView):
    """Patient's own booking history."""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Booking.objects.filter(patient=self.request.user).order_by("-created_at")


class HospitalBookingsView(generics.ListAPIView):
    """Hospital admin's view of bookings made against their hospital — this is what
    populates the 'pending requests' dashboard (Day 10)."""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalStaff]

    def get_queryset(self):
        qs = Booking.objects.filter(hospital_id=self.request.user.hospital_id).order_by("-created_at")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Booking.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        is_owner_patient = user.role == "patient" and obj.patient_id == user.id
        is_owner_hospital_staff = user.role in ("hospital_admin", "doctor") and obj.hospital_id == user.hospital_id
        if not (is_owner_patient or is_owner_hospital_staff):
            raise PermissionDenied("You don't have access to this booking.")
        return obj


class TransitionBookingView(APIView):
    """
    Status-change endpoint used by both roles:
    - Patient: cancel their own booking
    - Hospital admin/doctor: confirm, reject, mark completed, or mark no-show for their hospital's bookings
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        booking = generics.get_object_or_404(Booking, pk=pk)
        serializer = TransitionBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        note = serializer.validated_data.get("note", "")

        user = request.user
        if user.role == "patient":
            if booking.patient_id != user.id:
                raise PermissionDenied("This isn't your booking.")
            if new_status not in PATIENT_ALLOWED_TARGETS:
                raise PermissionDenied("Patients can only cancel a booking.")
        elif user.role in ("hospital_admin", "doctor"):
            if booking.hospital_id != user.hospital_id:
                raise PermissionDenied("This booking doesn't belong to your hospital.")
            if new_status not in HOSPITAL_STAFF_ALLOWED_TARGETS:
                raise PermissionDenied("Hospital staff cannot set this status.")
        else:
            raise PermissionDenied("Your role cannot modify bookings.")

        try:
            updated = transition_booking(booking, new_status, changed_by=user, note=note)
        except InvalidTransitionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NoBedAvailableError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(BookingSerializer(updated).data)
