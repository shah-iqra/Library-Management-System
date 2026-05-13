from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class ReportsMonitoringTest(TestCase):

    def setUp(self):

        User = get_user_model()

        self.user = User.objects.create_user(
            username="adminuser",
            email="admin@gmail.com",
            password="testpass123"
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.client.login(
            username="adminuser",
            password="testpass123"
        )

    def test_reports_analytics_page_opens(self):

        response = self.client.get(reverse("reports_analytics"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/reports_analytics.html")

    def test_system_monitoring_page_opens(self):

        response = self.client.get(reverse("system_monitoring"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/system_monitoring.html")

    def test_premium_content_page_opens(self):

        response = self.client.get(reverse("premium_content"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/premium_content.html")