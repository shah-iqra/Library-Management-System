from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from library.models import Member


class MemberTest(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="memberuser",
            email="member@gmail.com",
            password="testpass123"
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.client.login(
            username="memberuser",
            password="testpass123"
        )

        self.member = Member.objects.create(
            user=self.user,
            address="Dhaka, Bangladesh",
            membership_type="basic",
            emergency_contact="01700000000"
        )

    def test_member_created(self):
        self.assertEqual(self.member.user.username, "memberuser")
        self.assertEqual(self.member.address, "Dhaka, Bangladesh")
        self.assertEqual(self.member.membership_type, "basic")
        self.assertTrue(self.member.is_active)

    def test_member_string_method(self):
        self.assertEqual(str(self.member), "memberuser")

    def test_member_list_page_opens(self):
        response = self.client.get(reverse("member_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "library/member_list.html")