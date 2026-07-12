from django.urls import path

from .views import (
    BookingDetailView,
    CreateBookingView,
    CreateEmergencyBookingView,
    HospitalAnalyticsExportView,
    HospitalAnalyticsView,
    HospitalBookingsView,
    MyBookingsView,
    TransitionBookingView,
    VerifyPaymentView,
)

app_name = "bookings"

urlpatterns = [
    path("", CreateBookingView.as_view(), name="create"),
    path("emergency/", CreateEmergencyBookingView.as_view(), name="create-emergency"),
    path("mine/", MyBookingsView.as_view(), name="mine"),
    path("hospital/", HospitalBookingsView.as_view(), name="hospital-list"),
    path("hospital/analytics/", HospitalAnalyticsView.as_view(), name="hospital-analytics"),
    path("hospital/analytics/export/", HospitalAnalyticsExportView.as_view(), name="hospital-analytics-export"),
    path("<int:pk>/", BookingDetailView.as_view(), name="detail"),
    path("<int:pk>/transition/", TransitionBookingView.as_view(), name="transition"),
    path("<int:pk>/verify-payment/", VerifyPaymentView.as_view(), name="verify-payment"),
]
