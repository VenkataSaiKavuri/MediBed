from django.urls import path

from .fraud_views import (
    ClearBookingFlagView,
    FlaggedUsersListView,
    FraudDashboardSummaryView,
    PendingIdentityDocumentsListView,
    ReviewIdentityDocumentView,
    SuspiciousBookingsListView,
    UnflagUserView,
)

app_name = "core"

urlpatterns = [
    path("summary/", FraudDashboardSummaryView.as_view(), name="fraud-summary"),
    path("flagged-users/", FlaggedUsersListView.as_view(), name="flagged-users"),
    path("flagged-users/<int:pk>/unflag/", UnflagUserView.as_view(), name="unflag-user"),
    path("suspicious-bookings/", SuspiciousBookingsListView.as_view(), name="suspicious-bookings"),
    path("suspicious-bookings/<int:pk>/clear/", ClearBookingFlagView.as_view(), name="clear-booking-flag"),
    path("pending-documents/", PendingIdentityDocumentsListView.as_view(), name="pending-documents"),
    path("pending-documents/<int:pk>/review/", ReviewIdentityDocumentView.as_view(), name="review-document"),
]
