from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from library.models import Category


class CategoryTest(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="categoryuser",
            email="category@gmail.com",
            password="testpass123"
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.client.login(
            username="categoryuser",
            password="testpass123"
        )

        self.category = Category.objects.create(
            name="Computer Science"
        )

    def test_category_created(self):
        self.assertEqual(self.category.name, "Computer Science")

    def test_category_list_page_opens(self):
        response = self.client.get(reverse("category_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/category_list.html")