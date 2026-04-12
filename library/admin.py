from django.contrib import admin
from .models import Book, Member, Borrow

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'total_copies', 'available_copies']
    search_fields = ['title', 'author', 'isbn']

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'joined_date']
    search_fields = ['name', 'email']

@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ['book', 'member', 'borrow_date', 'return_date', 'is_returned']
    list_filter = ['is_returned']