from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingSerializer
from apps.core.permissions import IsPlatformAdmin
from apps.users.models import IdentityDocument, User

from .fraud_serializers import (
    FlaggedUserSerializer,
    IdentityDocumentReviewSerializer,
    ReviewActionSerializer,
    SuspiciousBookingSerializer,
)


class FraudDashboardSummaryView(APIView):
    """Single call for the dashboard's top-level counts, so the UI can show badges
    without firing three separate requests just to render tab counts."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        return Response({
            "flagged_users_count": User.objects.filter(is_flagged=True).count(),
            "suspicious_bookings_count": Booking.objects.filter(is_suspicious=True).count(),
            "pending_documents_count": IdentityDocument.objects.filter(reviewed=False).exclude(
                name_match_result="exact_match"
            ).count(),
        })


class FlaggedUsersListView(generics.ListAPIView):
    """All patients currently flagged for restricted booking privileges (Day 16)."""
    serializer_class = FlaggedUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.filter(is_flagged=True).order_by("-no_show_count")


class UnflagUserView(APIView):
    """Manually restores a user's instant-booking privileges — the actual 'block' side of
    Day 16's flagging system already happens automatically; this is the 'un-block' side,
    for when a platform admin reviews a case and decides the flag was unwarranted or the
    user has been sufficiently warned."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def post(self, request, pk):
        user = generics.get_object_or_404(User, pk=pk)
        user.is_flagged = False
        user.save(update_fields=["is_flagged"])
        return Response(FlaggedUserSerializer(user).data)


class SuspiciousBookingsListView(generics.ListAPIView):
    """All bookings flagged by Day 17's soft fraud signals (device/IP sharing, rapid-fire)."""
    serializer_class = SuspiciousBookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = Booking.objects.filter(is_suspicious=True).order_by("-created_at")


class ClearBookingFlagView(APIView):
    """Platform admin reviewed a suspicious booking and judged it legitimate — clears the
    flag without touching the booking's actual status (confirm/reject/etc. still happens
    through the normal hospital admin flow, unaffected by this)."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def post(self, request, pk):
        booking = generics.get_object_or_404(Booking, pk=pk)
        booking.is_suspicious = False
        booking.save(update_fields=["is_suspicious"])
        return Response(BookingSerializer(booking).data)


class PendingIdentityDocumentsListView(generics.ListAPIView):
    """Documents needing a human look — anything not already an automatic exact_match,
    and not yet reviewed."""
    serializer_class = IdentityDocumentReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = (
        IdentityDocument.objects.filter(reviewed=False)
        .exclude(name_match_result="exact_match")
        .order_by("uploaded_at")
    )


class ReviewIdentityDocumentView(APIView):
    """Platform admin approves (manually confirms the identity despite a name mismatch —
    e.g. a legitimate nickname/transliteration difference) or rejects (leaves unverified,
    e.g. genuinely looks like someone else's document) a pending document."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def post(self, request, pk):
        doc = generics.get_object_or_404(IdentityDocument, pk=pk)
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        doc.reviewed = True
        doc.reviewed_by = request.user
        doc.reviewed_at = timezone.now()
        doc.save(update_fields=["reviewed", "reviewed_by", "reviewed_at"])

        if action == "approve":
            doc.user.id_document_verified = True
            doc.user.save(update_fields=["id_document_verified"])

        return Response(IdentityDocumentReviewSerializer(doc).data)
