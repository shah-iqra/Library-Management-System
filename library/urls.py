from django.urls import path
from . import views

urlpatterns = [
    # Auth URLs
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Book URLs
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/edit/<int:pk>/', views.book_edit, name='book_edit'),
    path('books/delete/<int:pk>/', views.book_delete, name='book_delete'),

    # Member Management URLs (এগুলো নিশ্চিত করুন)
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.member_add, name='member_add'),
    path('members/edit/<int:pk>/', views.member_edit, name='member_edit'),
    path('members/delete/<int:pk>/', views.member_delete, name='member_delete'),

    # Borrowing URLs
    path('borrow/', views.borrow_book, name='borrow_book'),
    path('borrows/', views.borrow_list, name='borrow_list'),
    path('return/<int:pk>/', views.return_book, name='return_book'),
]