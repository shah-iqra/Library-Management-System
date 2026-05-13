from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


class PaymentSeleniumTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Edge()
        self.browser.maximize_window()

        User = get_user_model()

        self.user = User.objects.create_user(
            username="paymentuser",
            password="testpass123"
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

    def tearDown(self):
        time.sleep(10)
        self.browser.quit()

    def login(self):
        self.browser.get(self.live_server_url + "/login/")

        self.browser.find_element(By.NAME, "username").send_keys("paymentuser")
        self.browser.find_element(By.NAME, "password").send_keys("testpass123")

        self.browser.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

        time.sleep(1)

    def test_user_can_make_payment(self):
        self.login()

        self.browser.get(self.live_server_url + "/online-payment/")

        time.sleep(1)

        self.browser.find_element(By.NAME, "amount").send_keys("500")
        self.browser.find_element(By.NAME, "method").send_keys("bKash")
        self.browser.find_element(By.NAME, "transaction_id").send_keys("TXN123456")

        self.browser.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        ).click()

        time.sleep(2)

        self.assertIn("Payment", self.browser.page_source)
        self.assertIn("TXN123456", self.browser.page_source)