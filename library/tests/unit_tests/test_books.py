from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from library.models import Book


class BookTest(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="bookuser",
            email="bookuser@gmail.com",
            password="testpass123"
        )

        self.client.login(
            username="bookuser",
            password="testpass123"
        )

        self.book = Book.objects.create(
            title="Python Basics",
            author="Mainul",
            isbn="123456789"
        )

    def test_book_created(self):
        self.assertEqual(self.book.title, "Python Basics")
        self.assertEqual(self.book.author, "Mainul")
        self.assertEqual(self.book.isbn, "123456789")

    def test_book_list_page_opens(self):
        response = self.client.get(reverse("book_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/book_list.html")

    def test_book_detail_page_opens(self):
        response = self.client.get(reverse("book_detail", args=[self.book.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/book_detail.html")