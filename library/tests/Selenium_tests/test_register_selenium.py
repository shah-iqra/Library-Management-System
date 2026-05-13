from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


class RegisterSeleniumTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Edge()
        self.browser.maximize_window()

    def tearDown(self):
        time.sleep(10)
        self.browser.quit()

    def test_user_can_register(self):
        self.browser.get(self.live_server_url + "/register/")

        self.browser.find_element(By.NAME, "username").send_keys("newuser")
        self.browser.find_element(By.NAME, "email").send_keys("newuser@gmail.com")
        self.browser.find_element(By.NAME, "first_name").send_keys("New")
        self.browser.find_element(By.NAME, "last_name").send_keys("User")
        self.browser.find_element(By.NAME, "password1").send_keys("testpass123")
        self.browser.find_element(By.NAME, "password2").send_keys("testpass123")

        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        time.sleep(2)

        self.assertIn("/login", self.browser.current_url)