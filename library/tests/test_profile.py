from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class ProfileTest(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@gmail.com",
            password="testpass123"
        )

        self.client.login(
            username="profileuser",
            password="testpass123"
        )

    def test_profile_page_opens(self):
        response = self.client.get(reverse("manage_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/manage_profile.html")

    def test_change_password_page_opens(self):
        response = self.client.get(reverse("change_password"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/change_password.html")