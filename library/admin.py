from django.contrib import admin
from .models import Category, Book, Member, Transaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['code_no', 'title', 'author', 'category', 'total_copies', 'available_copies', 'added_on']
    search_fields = ['title', 'code_no', 'author', 'isbn']
    list_filter = ['category']

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'membership_type', 'membership_start', 'membership_end']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'issue_date', 'due_date', 'return_date', 'status', 'fine', 'fine_paid']
    list_filter = ['status', 'fine_paid']
    search_fields = ['book__title', 'user__username']
