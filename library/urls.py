from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('manage-profile/', views.manage_profile, name='manage_profile'),
    path('change-password/', views.change_password, name='change_password'),

    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/edit/<int:pk>/', views.book_edit, name='book_edit'),
    path('books/delete/<int:pk>/', views.book_delete, name='book_delete'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),

    path('digital-resources/', views.digital_resources, name='digital_resources'),
    path('digital-resources/add/', views.digital_resource_add, name='digital_resource_add'),
    path('digital-resources/edit/<int:pk>/', views.digital_resource_edit, name='digital_resource_edit'),
    path('digital-resources/delete/<int:pk>/', views.digital_resource_delete, name='digital_resource_delete'),
    path('digital-resources/read/<int:pk>/', views.digital_resource_read, name='digital_resource_read'),
    path('digital-resources/download/<int:pk>/', views.digital_resource_download, name='digital_resource_download'),

    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.member_add, name='member_add'),
    path('members/edit/<int:pk>/', views.member_edit, name='member_edit'),
    path('members/delete/<int:pk>/', views.member_delete, name='member_delete'),

    path('borrow/', views.borrow_book, name='borrow_book'),
    path('borrows/', views.borrow_list, name='borrow_list'),
    path('return/<int:pk>/', views.return_book, name='return_book'),

    path('research-papers/', views.research_papers, name='research_papers'),
    path('premium-content/', views.premium_content, name='premium_content'),
    path('online-payment/', views.online_payment, name='online_payment'),
    path('fines-dues/', views.fines_dues, name='fines_dues'),
    path('system-monitoring/', views.system_monitoring, name='system_monitoring'),
    path('reports-analytics/', views.reports_analytics, name='reports_analytics'),

    path('librarian/research-papers/', views.manage_research_papers, name='manage_research_papers'),
    path('librarian/research-papers/upload/', views.upload_research_paper, name='upload_research_paper'),
    path('librarian/research-papers/approval/', views.approval_access_control, name='approval_access_control'),
    path('librarian/research-papers/approve/<int:paper_id>/', views.approve_paper, name='approve_paper'),
    path('librarian/research-papers/reject/<int:paper_id>/', views.reject_paper, name='reject_paper'),

    path('papers/', views.approved_paper_list, name='approved_paper_list'),
    path('papers/<int:paper_id>/', views.paper_detail, name='paper_detail'),
    path('papers/<int:paper_id>/read/', views.read_paper, name='read_paper'),
    path('papers/<int:paper_id>/download/', views.download_paper, name='download_paper'),
]