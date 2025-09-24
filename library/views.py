from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User

from .models import Book, Transaction, Member, Category
from .forms import BookSearchForm, IssueForm, ReturnForm, AddBookForm, AddUserForm

LOAN_DAYS = 14
FINE_PER_DAY = Decimal('5.00')


@login_required
def home(request):
    if request.user.is_staff:
        return redirect('admin_home')
    return redirect('user_home')


@login_required
def admin_home(request):
    if not request.user.is_staff:
        return redirect('user_home')
    
    books_count = Book.objects.count()
    issued_count = Transaction.objects.filter(status='issued', user__is_staff=False).count()
    recent_tx = Transaction.objects.filter(user__is_staff=False).order_by('-issue_date')[:8]
    return render(request, 'library/admin_home.html', {
        'books_count': books_count,
        'issued_count': issued_count,
        'recent_tx': recent_tx,
    })


@login_required
def user_home(request):
    if request.user.is_staff:
        return redirect('admin_home')
    
    my_issued = Transaction.objects.filter(user=request.user).order_by('-issue_date')
    return render(request, 'library/user_home.html', {'my_issued': my_issued})


@login_required
def book_availability(request):
    form = BookSearchForm(request.GET or None)
    books = Book.objects.all().order_by('title')
    if form.is_valid() and form.cleaned_data.get('q'):
        q = form.cleaned_data['q']
        books = books.filter(title__icontains=q)
    return render(request, 'library/book_availability.html', {'books': books, 'form': form})


@login_required
def issue_book(request):
    # Admin users should only issue books to other users, not themselves
    if request.user.is_staff:
        preselect_id = request.GET.get('book')
        if request.method == 'POST':
            form = IssueForm(request.POST, current_user=request.user)
            if form.is_valid():
                book = form.cleaned_data['book']
                target_user = form.cleaned_data['user']
                
                if target_user.is_staff:
                    messages.error(request, "Cannot issue books to admin users.")
                    return redirect('admin_home')

                if book.available_copies <= 0:
                    messages.error(request, "Book is not available for issuing.")
                    return redirect('book_availability')

                with db_transaction.atomic():
                    if book.available_copies <= 0:
                        messages.error(request, "Book became unavailable. Try again.")
                        return redirect('book_availability')
                    book.available_copies = book.available_copies - 1
                    book.save()

                    issue_date = date.today()
                    due_date = issue_date + timedelta(days=LOAN_DAYS)
                    tx = Transaction.objects.create(
                        user=target_user,
                        book=book,
                        issue_date=issue_date,
                        due_date=due_date
                    )

                messages.success(request, f"Issued '{book.title}' to {target_user.username}. Due on {due_date}.")
                return redirect('admin_home')
        else:
            initial = {}
            if preselect_id:
                try:
                    pre_book = Book.objects.get(id=preselect_id)
                    initial['book'] = pre_book
                except Book.DoesNotExist:
                    pass
            form = IssueForm(initial=initial, current_user=request.user)

        return render(request, 'library/issue_book.html', {'form': form, 'is_admin': True})
    
    else:
        # Regular users can issue books to themselves
        preselect_id = request.GET.get('book')
        if request.method == 'POST':
            form = IssueForm(request.POST, current_user=request.user)
            if form.is_valid():
                book = form.cleaned_data['book']
                target_user = request.user

                if book.available_copies <= 0:
                    messages.error(request, "Book is not available for issuing.")
                    return redirect('book_availability')

                with db_transaction.atomic():
                    if book.available_copies <= 0:
                        messages.error(request, "Book became unavailable. Try again.")
                        return redirect('book_availability')
                    book.available_copies = book.available_copies - 1
                    book.save()

                    issue_date = date.today()
                    due_date = issue_date + timedelta(days=LOAN_DAYS)
                    tx = Transaction.objects.create(
                        user=target_user,
                        book=book,
                        issue_date=issue_date,
                        due_date=due_date
                    )

                messages.success(request, f"Issued '{book.title}' to you. Due on {due_date}.")
                return redirect('user_home')
        else:
            initial = {}
            if preselect_id:
                try:
                    pre_book = Book.objects.get(id=preselect_id)
                    initial['book'] = pre_book
                except Book.DoesNotExist:
                    pass
            form = IssueForm(initial=initial, current_user=request.user)

        return render(request, 'library/issue_book.html', {'form': form, 'is_admin': False})


@login_required
def return_book(request, tx_id):
    tx = get_object_or_404(Transaction, id=tx_id)

    if not request.user.is_staff and tx.user != request.user:
        messages.error(request, "You are not authorized to return this transaction.")
        return redirect('user_home')
    
    if request.user.is_staff and tx.user.is_staff:
        messages.error(request, "Admin users cannot issue books to themselves.")
        return redirect('admin_home')

    if tx.status != 'issued':
        messages.info(request, "This transaction is already returned.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    if request.method == 'POST':
        tx.return_date = date.today()
        tx.fine = tx.calculate_fine(per_day=FINE_PER_DAY)
        tx.status = 'returned'
        tx.save()

        with db_transaction.atomic():
            book = tx.book
            book.available_copies = book.available_copies + 1
            if book.available_copies > book.total_copies:
                book.available_copies = book.total_copies
            book.save()

        if tx.fine > 0:
            messages.warning(request, f"Book returned. Fine due: ₹{tx.fine}. Use Pay Fine to mark payment.")
        else:
            messages.success(request, "Book returned successfully. No fine.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    return render(request, 'library/confirm_return.html', {'tx': tx})


@login_required
def pay_fine(request, tx_id):
    tx = get_object_or_404(Transaction, id=tx_id)

    if not request.user.is_staff and tx.user != request.user:
        messages.error(request, "You are not authorized to pay this fine.")
        return redirect('user_home')
    
    if request.user.is_staff and tx.user.is_staff:
        messages.error(request, "Admin users cannot have transactions.")
        return redirect('admin_home')

    if tx.fine <= 0:
        messages.info(request, "No fine due for this transaction.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    if request.method == 'POST':
        # Simulated payment: mark paid
        tx.fine_paid = True
        tx.save()
        messages.success(request, f"Fine of ₹{tx.fine} marked as paid.")
        if request.user.is_staff:
            return redirect('admin_home')
        return redirect('user_home')

    return render(request, 'library/pay_fine.html', {'tx': tx})


@login_required
def add_book(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to add books.")
        return redirect('user_home')
    
    if request.method == 'POST':
        form = AddBookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' added successfully!")
            return redirect('admin_home')
    else:
        form = AddBookForm()
    
    return render(request, 'library/add_book.html', {'form': form})


@login_required
def add_user(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to add users.")
        return redirect('user_home')
    
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            membership_type = form.cleaned_data['membership_type']
            membership_start = date.today()
            
            if membership_type == '6m':
                membership_end = membership_start + timedelta(days=180)
            elif membership_type == '1y':
                membership_end = membership_start + timedelta(days=365)
            elif membership_type == '2y':
                membership_end = membership_start + timedelta(days=730)
            
            Member.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', ''),
                adhaar=form.cleaned_data.get('adhaar', ''),
                membership_type=membership_type,
                membership_start=membership_start,
                membership_end=membership_end
            )
            
            messages.success(request, f"User '{user.username}' added successfully!")
            return redirect('admin_home')
    else:
        form = AddUserForm()
    
    return render(request, 'library/add_user.html', {'form': form})


@login_required
def manage_categories(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to manage categories.")
        return redirect('user_home')
    
    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        if category_name:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                messages.success(request, f"Category '{category_name}' added successfully!")
            else:
                messages.info(request, f"Category '{category_name}' already exists.")
        else:
            messages.error(request, "Please enter a category name.")
    
    categories = Category.objects.all().order_by('name')
    return render(request, 'library/manage_categories.html', {'categories': categories})
