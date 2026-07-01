from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .otp_utils import generate_and_send_otp, verify_otp
from .serializers import (
    CustomTokenObtainPairSerializer,
    RequestOTPSerializer,
    SignupSerializer,
    VerifyOTPSerializer,
)

User = get_user_model()


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Auto-send an OTP right after signup so the frontend can go straight to verification
        generate_and_send_otp(user.phone_number, purpose="signup")
        return Response(
            {"message": "Signup successful. OTP sent to phone.", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_request"  # 5/hour, set in settings.py — prevents SMS-bombing abuse

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        generate_and_send_otp(**serializer.validated_data)
        return Response({"message": "OTP sent."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success, message = verify_otp(**serializer.validated_data)

        if success and serializer.validated_data["purpose"] == "signup":
            User.objects.filter(
                phone_number=serializer.validated_data["phone_number"]
            ).update(phone_verified=True)

        if not success:
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": message}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Login endpoint — returns access/refresh JWT tokens with role embedded."""
    serializer_class = CustomTokenObtainPairSerializer
