from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.core.files.uploadedfile import SimpleUploadedFile
from library.models import ResearchPaper

import time
import os


class ResearchPaperUploadSeleniumTest(StaticLiveServerTestCase):

    def setUp(self):

        options = webdriver.EdgeOptions()
        options.add_argument("--window-size=1600,900")
        options.add_argument("--force-device-scale-factor=0.8")

        self.browser = webdriver.Edge(options=options)

        User = get_user_model()

        self.user = User.objects.create_user(
            username="admin",
            password="testpass123",
            is_staff=True,
            is_superuser=True
        )

        # Fake PDF create
        self.test_pdf_path = os.path.abspath(
            "test_upload_paper.pdf"
        )

        with open(self.test_pdf_path, "wb") as file:
            file.write(
                b"%PDF-1.4 Selenium Test PDF File"
            )

    def tearDown(self):

        time.sleep(10)

        self.browser.quit()

        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)

    # Login function
    def login(self):

        self.browser.get(
            self.live_server_url + "/login/"
        )

        time.sleep(3)

        self.browser.find_element(
            By.NAME,
            "username"
        ).send_keys("admin")

        self.browser.find_element(
            By.NAME,
            "password"
        ).send_keys("testpass123")

        self.browser.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

        time.sleep(4)

    # Upload research paper test
    def test_user_can_upload_research_paper(self):

        self.login()

        self.browser.get(
            self.live_server_url +
            "/librarian/research-papers/upload/"
        )

        time.sleep(4)

        # Fill form
        self.browser.find_element(
            By.NAME,
            "title"
        ).send_keys(
            "Selenium Test Research Paper"
        )

        self.browser.find_element(
            By.NAME,
            "author"
        ).send_keys(
            "Mainul"
        )

        self.browser.find_element(
            By.NAME,
            "journal"
        ).send_keys(
            "Test Journal"
        )

        self.browser.find_element(
            By.NAME,
            "year"
        ).send_keys(
            "2026"
        )

        self.browser.find_element(
            By.NAME,
            "abstract"
        ).send_keys(
            "This research paper was uploaded using Selenium automated testing."
        )

        # Upload PDF
        self.browser.find_element(
            By.NAME,
            "paper_file"
        ).send_keys(
            self.test_pdf_path
        )

        time.sleep(2)

        # Submit form
        self.browser.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

        time.sleep(5)

        # Database check
        paper_exists = ResearchPaper.objects.filter(
            title="Selenium Test Research Paper"
        ).exists()

        self.assertTrue(paper_exists)

        input("Press Enter to close browser...")