from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date


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

    profile_picture = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


# ২. Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# ৩. Book Model
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books'
    )
    description = models.TextField(null=True, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    cover_image = models.ImageField(
        upload_to='book_covers/',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


# ৪. Member Model
class Member(models.Model):
    MEMBERSHIP_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('student', 'Student'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    address = models.TextField(null=True, blank=True)
    joined_date = models.DateField(auto_now_add=True)

    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_CHOICES,
        default='basic'
    )
    membership_expiry = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=15, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

    def is_membership_valid(self):
        if self.membership_expiry:
            return date.today() <= self.membership_expiry
        return True

    def active_borrows_count(self):
        return self.user.borrowed_books.filter(is_returned=False).count()


# ৫. Borrow Model
class Borrow(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    ]

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

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='borrowed'
    )
    fine_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00
    )
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.book.title} borrowed by {self.member.username}"

    def is_overdue(self):
        if not self.is_returned and self.due_date:
            return date.today() > self.due_date
        return False

    def calculate_fine(self):
        if self.is_overdue():
            overdue_days = (date.today() - self.due_date).days
            return overdue_days * 5
        return 0

    def save(self, *args, **kwargs):
        if self.is_overdue():
            self.status = 'overdue'
            self.fine_amount = self.calculate_fine()
        if self.is_returned and self.status != 'lost':
            self.status = 'returned'
        super().save(*args, **kwargs)


# ৬. ResearchPaper Model
class ResearchPaper(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    journal = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    abstract = models.TextField(blank=True, null=True)
    paper_file = models.FileField(upload_to='research_papers/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title