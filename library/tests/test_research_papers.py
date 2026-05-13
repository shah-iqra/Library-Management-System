from django.test import TestCase
from django.urls import reverse


class ResearchPaperTest(TestCase):

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