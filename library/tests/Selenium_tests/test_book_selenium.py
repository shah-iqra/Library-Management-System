from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from library.models import Book
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


class BookSeleniumTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Edge()
        self.browser.maximize_window()

        User = get_user_model()

        self.user = User.objects.create_user(
            username="bookuser",
            password="testpass123"
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        Book.objects.create(
            title="Python Basics",
            author="Mainul",
            isbn="123456789"
        )

    def tearDown(self):

        time.sleep(10)   # Browser 10 seconds open থাকবে

        self.browser.quit()

    def login(self):

        self.browser.get(self.live_server_url + "/login/")

        self.browser.find_element(
            By.NAME,
            "username"
        ).send_keys("bookuser")

        self.browser.find_element(
            By.NAME,
            "password"
        ).send_keys("testpass123")

        self.browser.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

        time.sleep(1)

    def test_book_list_opens(self):

        self.login()

        self.browser.get(self.live_server_url + "/books/")

        time.sleep(2)

        self.assertIn("Python Basics", self.browser.page_source)