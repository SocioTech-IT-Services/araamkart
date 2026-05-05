"""DRF API Views — Users Auth"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout

from .models import User, OTPRecord
from .serializers import UserSerializer, RegisterSerializer
from apps.notifications.services import send_otp_console


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        d = s.validated_data
        email = d.get("email") or None
        phone = d.get("phone") or None
        if email and User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered."}, status=400)
        if phone and User.objects.filter(phone=phone).exists():
            return Response({"error": "Phone already registered."}, status=400)
        user = User.objects.create_user(
            email=email, phone=phone,
            password=d.get("password") or None,
            full_name=d["full_name"],
            business_name=d.get("business_name", ""),
        )
        otp = OTPRecord.generate_otp(user, purpose="register")
        send_otp_console(user, otp.otp_code)
        return Response({"message": "User registered. OTP sent.", "user_id": user.pk}, status=201)


class LoginPhoneAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone", "").strip()
        if not phone:
            return Response({"error": "Phone is required."}, status=400)
        user, _ = User.objects.get_or_create(phone=phone, defaults={"full_name": phone})
        otp = OTPRecord.generate_otp(user, purpose="login")
        send_otp_console(user, otp.otp_code)
        return Response({"message": "OTP sent.", "user_id": user.pk})


class LoginEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or password."}, status=400)
        if not user.check_password(password):
            return Response({"error": "Invalid email or password."}, status=400)
        otp = OTPRecord.generate_otp(user, purpose="login")
        send_otp_console(user, otp.otp_code)
        return Response({"message": "OTP sent.", "user_id": user.pk})


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        otp_code = request.data.get("otp_code", "").strip()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        record = OTPRecord.objects.filter(user=user, is_used=False).order_by("-created_at").first()
        if not record or not record.is_valid():
            return Response({"error": "OTP expired. Request a new one."}, status=400)
        if record.otp_code != otp_code:
            return Response({"error": "Invalid OTP."}, status=400)
        record.is_used = True
        record.save()
        if not user.is_verified:
            user.is_verified = True
            user.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response({"message": "Logged in.", "user": UserSerializer(user).data})


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out."})
