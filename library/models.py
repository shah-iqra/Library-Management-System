from django.db import models
from django.contrib.auth.models import AbstractUser

# ১. কাস্টম ইউজার মডেল (Role Based)
class User(AbstractUser):
    # রোলের নামগুলো কনস্ট্যান্ট হিসেবে রাখা ভালো প্র্যাকটিস
    ADMIN = 'admin'
    LIBRARIAN = 'librarian'
    REGULAR_USER = 'user'

    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (LIBRARIAN, 'Librarian'),
        (REGULAR_USER, 'Regular User'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=REGULAR_USER)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ২. বুক মডেল
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    description = models.TextField(null=True, blank=True) # বইয়ের সারসংক্ষেপের জন্য
    total_copies = models.PositiveIntegerField(default=1) # নেগেটিভ সংখ্যা এড়াতে PositiveIntegerField
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title


# ৩. প্রোফাইল বা মেম্বার মডেল 
# (যদি আলাদা ডাটা রাখতে চান যেমন অ্যাড্রেস বা মেম্বারশিপ লেভেল)
class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    address = models.TextField(null=True, blank=True)
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# ৪. বরো (Borrow) মডেল
class Borrow(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrows')
    # এখানে সরাসরি কাস্টম ইউজারকে কানেক্ট করা হয়েছে
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowed_books')
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True) # ফেরত দেওয়ার নির্দিষ্ট তারিখ
    return_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.book.title} borrowed by {self.member.username}"