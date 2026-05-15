from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class NotificationTest(TestCase):

    def setUp(self):

        User = get_user_model()

        self.user = User.objects.create_user(
            username="notificationuser",
            password="testpass123"
        )

    def test_notification_page_requires_login(self):

        response = self.client.get(
            reverse("notification_page")
        )

        self.assertNotEqual(response.status_code, 200)

    def test_notification_page_opens_after_login(self):

        self.client.login(
            username="notificationuser",
            password="testpass123"
        )

        response = self.client.get(
            reverse("notification_page")
        )

        self.assertEqual(response.status_code, 200)

    def test_notification_template_used(self):

        self.client.login(
            username="notificationuser",
            password="testpass123"
        )

        response = self.client.get(
            reverse("notification_page")
        )

        self.assertTemplateUsed(
            response,
            "library/notifications.html"
        )

    def test_notification_content_exists(self):

        self.client.login(
            username="notificationuser",
            password="testpass123"
        )

        response = self.client.get(
            reverse("notification_page")
        )

        self.assertContains(response, "Notification")