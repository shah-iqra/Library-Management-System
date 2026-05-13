from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from library.models import Payment


class PaymentTest(TestCase):

    def setUp(self):

        User = get_user_model()

        self.user = User.objects.create_user(
            username="paymentuser",
            email="payment@gmail.com",
            password="testpass123"
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.client.login(
            username="paymentuser",
            password="testpass123"
        )

        self.payment = Payment.objects.create(
            user=self.user,
            amount=500.00,
            method="bKash",
            transaction_id="TXN123456"
        )

    def test_payment_created(self):

        self.assertEqual(self.payment.user.username, "paymentuser")
        self.assertEqual(float(self.payment.amount), 500.00)
        self.assertEqual(self.payment.method, "bKash")
        self.assertEqual(self.payment.status, "Pending")

    def test_payment_string_method(self):

        expected = "paymentuser - TXN123456"

        self.assertEqual(str(self.payment), expected)

    def test_online_payment_page_opens(self):

        response = self.client.get(reverse("online_payment"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/online_payment.html")

    def test_payment_history_page_opens(self):

        response = self.client.get(reverse("payment_history"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/payment_history.html")

    def test_fines_dues_page_opens(self):

        response = self.client.get(reverse("fines_dues"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/fines_dues.html")