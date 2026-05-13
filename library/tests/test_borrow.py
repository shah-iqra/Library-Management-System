from django.test import TestCase
from django.urls import reverse
from library.models import Book, Member, Borrow


class BorrowTest(TestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title="Django Book",
            author="Mainul",
            isbn="987654321",
            quantity=3
        )

        self.member = Member.objects.create(
            name="Test Member",
            email="member@gmail.com",
            phone="01700000000"
        )

        self.borrow = Borrow.objects.create(
            book=self.book,
            member=self.member
        )

    def test_borrow_created(self):
        self.assertEqual(self.borrow.book.title, "Django Book")
        self.assertEqual(self.borrow.member.name, "Test Member")

    def test_borrow_list_page_opens(self):
        response = self.client.get(reverse("borrow_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/borrow_list.html")