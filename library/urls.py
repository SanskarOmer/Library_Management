from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('user-home/', views.user_home, name='user_home'),
    path('books/', views.book_availability, name='book_availability'),
    path('issue/', views.issue_book, name='issue_book'),
    path('return/<int:tx_id>/', views.return_book, name='return_book'),
    path('pay-fine/<int:tx_id>/', views.pay_fine, name='pay_fine'),
    path('add-book/', views.add_book, name='add_book'),
    path('add-user/', views.add_user, name='add_user'),
    path('manage-categories/', views.manage_categories, name='manage_categories'),
]
