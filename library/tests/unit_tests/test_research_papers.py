from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class ResearchPaperTest(TestCase):

    def setUp(self):

        User = get_user_model()

        self.user = User.objects.create_user(
            username="researchuser",
            password="testpass123"
        )

        self.admin = User.objects.create_user(
            username="adminresearch",
            password="testpass123",
            is_staff=True,
            is_superuser=True
        )

    def test_research_papers_page_opens(self):

        self.client.login(
            username="researchuser",
            password="testpass123"
        )

        response = self.client.get(reverse("research_papers"))

        self.assertEqual(response.status_code, 200)

    def test_approved_paper_list_page_opens(self):

        response = self.client.get(reverse("approved_paper_list"))

        self.assertEqual(response.status_code, 200)

    def test_manage_research_papers_requires_login(self):

        response = self.client.get(reverse("manage_research_papers"))

        self.assertNotEqual(response.status_code, 200)

    def test_manage_research_papers_opens_for_admin(self):

        self.client.login(
            username="adminresearch",
            password="testpass123"
        )

        response = self.client.get(reverse("manage_research_papers"))

        self.assertEqual(response.status_code, 200)

    def test_upload_research_paper_page_opens_for_admin(self):

        self.client.login(
            username="adminresearch",
            password="testpass123"
        )

        response = self.client.get(reverse("upload_research_paper"))

        self.assertEqual(response.status_code, 200)

    def test_approval_access_control_page_opens_for_admin(self):

        self.client.login(
            username="adminresearch",
            password="testpass123"
        )

        response = self.client.get(reverse("approval_access_control"))

        self.assertEqual(response.status_code, 200)