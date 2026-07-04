from django.urls import path

from .views import (
    BookingDetailView,
    CreateBookingView,
    HospitalBookingsView,
    MyBookingsView,
    TransitionBookingView,
    VerifyPaymentView,
)

app_name = "bookings"

urlpatterns = [
    path("", CreateBookingView.as_view(), name="create"),
    path("mine/", MyBookingsView.as_view(), name="mine"),
    path("hospital/", HospitalBookingsView.as_view(), name="hospital-list"),
    path("<int:pk>/", BookingDetailView.as_view(), name="detail"),
    path("<int:pk>/transition/", TransitionBookingView.as_view(), name="transition"),
    path("<int:pk>/verify-payment/", VerifyPaymentView.as_view(), name="verify-payment"),
]
