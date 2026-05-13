from django.test import SimpleTestCase
from django.urls import reverse, resolve
from library import views


class UrlTest(SimpleTestCase):

    def test_home_url(self):

        url = reverse("home")

        self.assertEqual(resolve(url).func, views.home)

    def test_login_url(self):

        url = reverse("login")

        self.assertEqual(resolve(url).func, views.login_view)

    def test_register_view_url(self):

        url = reverse("register")

        self.assertEqual(resolve(url).func, views.register_view)

    def test_book_list_url(self):

        url = reverse("book_list")

        self.assertEqual(resolve(url).func, views.book_list)

    def test_member_list_url(self):

        url = reverse("member_list")

        self.assertEqual(resolve(url).func, views.member_list)

    def test_borrow_list_url(self):

        url = reverse("borrow_list")

        self.assertEqual(resolve(url).func, views.borrow_list)