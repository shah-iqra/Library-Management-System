from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class WishlistTest(TestCase):

    def setUp(self):

        User = get_user_model()

        self.user = User.objects.create_user(
            username="wishlistuser",
            password="testpass123"
        )

    # Login ছাড়া access block হয় কিনা
    def test_wishlist_requires_login(self):

        response = self.client.get(reverse("wishlist_page"))

        self.assertNotEqual(response.status_code, 200)

    # Login এর পর page open হয় কিনা
    def test_wishlist_page_opens(self):

        self.client.login(
            username="wishlistuser",
            password="testpass123"
        )

        response = self.client.get(reverse("wishlist_page"))

        self.assertEqual(response.status_code, 200)

    # Correct template load হচ্ছে কিনা
    def test_wishlist_template_used(self):

        self.client.login(
            username="wishlistuser",
            password="testpass123"
        )

        response = self.client.get(reverse("wishlist_page"))

        self.assertTemplateUsed(
            response,
            "library/wishlist.html"
        )

    # Page content check
    def test_wishlist_content_exists(self):

        self.client.login(
            username="wishlistuser",
            password="testpass123"
        )

        response = self.client.get(reverse("wishlist_page"))

        self.assertContains(response, "Wishlist")