from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    DownloadIdentityDocumentView,
    MeView,
    MyIdentityDocumentsView,
    RegisterFCMTokenView,
    RequestOTPView,
    SignupView,
    UploadIdentityDocumentView,
    VerifyOTPView,
)

app_name = "users"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("otp/request/", RequestOTPView.as_view(), name="otp-request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("fcm-token/", RegisterFCMTokenView.as_view(), name="fcm-token"),
    path("identity-documents/", UploadIdentityDocumentView.as_view(), name="identity-upload"),
    path("identity-documents/mine/", MyIdentityDocumentsView.as_view(), name="identity-mine"),
    path("identity-documents/<int:pk>/download/", DownloadIdentityDocumentView.as_view(), name="identity-download"),
]
