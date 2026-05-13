from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class ResearchPaperTest(TestCase):

    def setUp(self):

        User = get_user_model()

        self.user = User.objects.create_user(
            username="researchuser",
            email="research@gmail.com",
            password="testpass123"
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.client.login(
            username="researchuser",
            password="testpass123"
        )

    def test_research_papers_page_opens(self):

        response = self.client.get(reverse("research_papers"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/research_papers.html")

    def test_upload_research_paper_page_opens(self):

        response = self.client.get(reverse("upload_research_paper"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/upload_research_paper.html")

    def test_manage_research_papers_page_opens(self):

        response = self.client.get(reverse("manage_research_papers"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/manage_research_papers.html")