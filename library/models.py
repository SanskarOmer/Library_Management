from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Book(models.Model):
    code_no = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    isbn = models.CharField(max_length=40, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    added_on = models.DateField(auto_now_add=True)

    def is_available(self):
        return self.available_copies > 0

    def __str__(self):
        return f"{self.title} ({self.code_no})"


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    adhaar = models.CharField(max_length=20, blank=True)

    MEMBERSHIP_CHOICES = [
        ('6m', '6 months'),
        ('1y', '1 year'),
        ('2y', '2 years'),
    ]
    membership_type = models.CharField(max_length=2, choices=MEMBERSHIP_CHOICES, default='1y')
    membership_start = models.DateField(null=True, blank=True)
    membership_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Transaction(models.Model):
    STATUS_CHOICES = [('issued', 'Issued'), ('returned', 'Returned')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(default=date.today)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    fine_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='issued')

    def calculate_fine(self, per_day=Decimal('5.00')):
        if not self.return_date:
            return Decimal('0.00')
        if self.return_date <= self.due_date:
            return Decimal('0.00')
        days = (self.return_date - self.due_date).days
        return per_day * Decimal(days)

    def __str__(self):
        return f"{self.book.title} -> {self.user.username} ({self.status})"
