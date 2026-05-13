from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


class LoginSeleniumTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Edge()
        self.browser.maximize_window()

        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@gmail.com",
            password="testpass123"
        )

    def tearDown(self):

        time.sleep(10)   # Browser 10 seconds open থাকবে

        self.browser.quit()

    def test_user_can_login(self):

        self.browser.get(self.live_server_url + "/login/")

        self.browser.find_element(By.NAME, "username").send_keys("testuser")

        self.browser.find_element(By.NAME, "password").send_keys("testpass123")

        self.browser.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

        time.sleep(2)

        self.assertNotIn("Login", self.browser.title)