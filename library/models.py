from django.db import models
from django.contrib.auth.models import AbstractUser


# ১. Custom User Model (Role Based)
class User(AbstractUser):
    ADMIN = 'admin'
    LIBRARIAN = 'librarian'
    REGULAR_USER = 'user'

    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (LIBRARIAN, 'Librarian'),
        (REGULAR_USER, 'Regular User'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=REGULAR_USER
    )
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ২. Book Model (UPDATED with image)
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)

    description = models.TextField(null=True, blank=True)

    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    # 📌 Book cover image
    cover_image = models.ImageField(
        upload_to='book_covers/',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


# ৩. Member Model
class Member(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    address = models.TextField(null=True, blank=True)
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# ৪. Borrow Model
class Borrow(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='borrows'
    )
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='borrowed_books'
    )

    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)

    is_returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.book.title} borrowed by {self.member.username}"