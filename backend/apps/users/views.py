from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.permissions import IsPatient

from .encryption import decrypt_bytes
from .models import IdentityDocument
from .otp_utils import generate_and_send_otp, verify_otp
from .serializers import (
    CustomTokenObtainPairSerializer,
    IdentityDocumentStatusSerializer,
    IdentityDocumentUploadSerializer,
    RequestOTPSerializer,
    SignupSerializer,
    UserProfileSerializer,
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


class MeView(APIView):
    """Returns the logged-in user's profile — used by the frontend on every page load
    to know role/hospital without re-decoding the JWT everywhere."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class RegisterFCMTokenView(APIView):
    """Frontend calls this once it has a Firebase device token, so push notifications
    (Day 12) have somewhere to be sent."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get("fcm_token", "")
        request.user.fcm_token = token
        request.user.save(update_fields=["fcm_token"])
        return Response({"message": "Token registered."})


class UploadIdentityDocumentView(APIView):
    """Patient uploads their Aadhaar/passport. Encrypted before being written to disk;
    the raw file is never stored or returned as-is."""
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = IdentityDocumentUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        doc = serializer.save()
        return Response(IdentityDocumentStatusSerializer(doc).data, status=201)


class MyIdentityDocumentsView(generics.ListAPIView):
    """Patient's own upload history/status — never exposes the encrypted file itself."""
    serializer_class = IdentityDocumentStatusSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        return IdentityDocument.objects.filter(user=self.request.user).order_by("-uploaded_at")


class DownloadIdentityDocumentView(APIView):
    """
    Strictly access-controlled: only the document's own patient, or a platform_admin
    (for manual review), can decrypt and download it. Never served via normal media URLs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        doc = generics.get_object_or_404(IdentityDocument, pk=pk)
        is_owner = doc.user_id == request.user.id
        is_platform_admin = request.user.role == "platform_admin"
        if not (is_owner or is_platform_admin):
            raise PermissionDenied("You don't have access to this document.")

        with doc.encrypted_file.open("rb") as f:
            encrypted_bytes = f.read()
        decrypted_bytes = decrypt_bytes(encrypted_bytes)

        response = HttpResponse(decrypted_bytes, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{doc.document_type}_{doc.user_id}"'
        return response
