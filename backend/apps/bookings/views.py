from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.permissions import IsHospitalStaff, IsPatient

from .models import Booking, BookingStatus
from .serializers import (
    BookingSerializer,
    CreateBookingSerializer,
    CreateEmergencyBookingSerializer,
    TransitionBookingSerializer,
    VerifyPaymentSerializer,
)
from .services import DepositNotPaidError, InvalidTransitionError, NoBedAvailableError, transition_booking
from .payments import verify_payment_amount, verify_payment_signature

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


class CreateEmergencyBookingView(generics.CreateAPIView):
    """
    Patient creates an emergency booking request — fast path, skips KYC (see
    CreateEmergencyBookingSerializer's docstring for the full list of what's intentionally
    skipped and why). Uses a separate, slightly looser throttle scope from regular bookings.
    """
    serializer_class = CreateEmergencyBookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "emergency_booking"  # 5/hour, set in settings.py since Day 1

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
        is_emergency_filter = self.request.query_params.get("is_emergency")
        if is_emergency_filter is not None:
            qs = qs.filter(is_emergency=is_emergency_filter.lower() == "true")
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
        except DepositNotPaidError as e:
            return Response({"detail": str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)

        return Response(BookingSerializer(updated).data)


class VerifyPaymentView(APIView):
    """Patient calls this right after completing the Razorpay checkout (or immediately,
    in dev-stub mode) to confirm the deposit was actually paid."""
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def post(self, request, pk):
        booking = generics.get_object_or_404(Booking, pk=pk, patient=request.user)

        # Guard 1: don't let a resolved booking be "paid" after the fact — a cancelled/
        # rejected booking is done, and a completed/no_show booking has already had its
        # deposit refunded or forfeited by this point, so re-marking it paid would be stale.
        if booking.status not in (BookingStatus.REQUESTED, BookingStatus.CONFIRMED, BookingStatus.ESCALATED):
            return Response(
                {"detail": f"This booking is '{booking.status}' and is no longer awaiting payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard 2: idempotent — if it's already paid, don't re-process (avoids a double-click
        # or retried request silently overwriting a valid payment_id with a new one).
        if booking.deposit_paid:
            return Response(BookingSerializer(booking).data)

        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_id = serializer.validated_data["razorpay_payment_id"]
        signature = serializer.validated_data.get("razorpay_signature", "")

        if not verify_payment_signature(booking.razorpay_order_id, payment_id, signature):
            return Response({"detail": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)

        if not verify_payment_amount(booking.razorpay_order_id, payment_id, booking.deposit_amount):
            return Response(
                {"detail": "Payment amount doesn't match the required deposit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.razorpay_payment_id = payment_id
        booking.deposit_paid = True
        booking.save(update_fields=["razorpay_payment_id", "deposit_paid"])

        return Response(BookingSerializer(booking).data)
