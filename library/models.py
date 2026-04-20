from django.db import models
from django.contrib.auth.models import AbstractUser

# ১. কাস্টম ইউজার মডেল (Role Based)
class User(AbstractUser):
    IS_ADMIN = 'admin'
    IS_LIBRARIAN = 'librarian'
    IS_USER = 'user'

    ROLE_CHOICES = [
        (IS_ADMIN, 'Administrator'),
        (IS_LIBRARIAN, 'Librarian'),
        (IS_USER, 'Regular User'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=IS_USER)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ২. বুক মডেল
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)

    def __str__(self):
        return self.title


# ৩. মেম্বার মডেল
class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# ৪. বরো (Borrow) মডেল
class Borrow(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.book.title} - {self.member.username}"