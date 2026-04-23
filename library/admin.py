from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Book, Member, Borrow, User, Category


# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'phone', 'role']
    list_filter = ['role']
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('role', 'phone')}),
    )


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


# Book Admin
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'isbn', 'total_copies', 'available_copies']
    search_fields = ['title', 'author', 'isbn']
    list_filter = ['category']


# Member Admin
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_email', 'get_phone', 'joined_date']
    search_fields = ['user__username', 'user__email']

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Phone'


# Borrow Admin
@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ['book', 'member', 'borrow_date', 'return_date', 'is_returned']
    list_filter = ['is_returned']