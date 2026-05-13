from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class AuthenticationTest(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@gmail.com",
            password="testpass123"
        )

    def test_login_page_opens(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/login.html")

    def test_register_page_opens(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/register.html")

    def test_user_can_login(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "testpass123"
        })

        self.assertEqual(response.status_code, 302)

    def test_wrong_password_cannot_login(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "wrongpass"
        })

        self.assertEqual(response.status_code, 200)