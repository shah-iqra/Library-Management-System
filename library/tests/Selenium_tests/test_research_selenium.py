from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


class ResearchSeleniumTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Edge()
        self.browser.maximize_window()

        User = get_user_model()
        self.user = User.objects.create_user(
            username="researchuser",
            password="testpass123"
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

    def tearDown(self):
        self.browser.quit()

    def login(self):
        self.browser.get(self.live_server_url + "/login/")
        self.browser.find_element(By.NAME, "username").send_keys("researchuser")
        self.browser.find_element(By.NAME, "password").send_keys("testpass123")
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

    def test_research_paper_page_opens(self):
        self.login()

        self.browser.get(self.live_server_url + "/research-papers/")

        time.sleep(2)

        self.assertIn("Research", self.browser.page_source)