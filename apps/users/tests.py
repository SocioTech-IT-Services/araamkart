from django.test import TestCase
from .models import User, OTPRecord
from django.utils import timezone
from datetime import timedelta

class UserAuthTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="9876543210",
            full_name="Test User",
            business_name="Test Business"
        )

    def test_otp_generation(self):
        otp = OTPRecord.generate_otp(self.user, purpose="login")
        self.assertEqual(len(otp.otp_code), 6)
        self.assertTrue(otp.otp_code.isdigit())
        self.assertEqual(otp.user, self.user)
        self.assertTrue(otp.is_valid())

    def test_otp_invalidation(self):
        otp1 = OTPRecord.generate_otp(self.user, purpose="login")
        otp2 = OTPRecord.generate_otp(self.user, purpose="login")
        
        otp1.refresh_from_db()
        self.assertTrue(otp1.is_used)  # Previous OTP should be marked as used/invalidated
        self.assertFalse(otp2.is_used)

    def test_otp_expiry(self):
        otp = OTPRecord.generate_otp(self.user, purpose="login")
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()
        self.assertFalse(otp.is_valid())
