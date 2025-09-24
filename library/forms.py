from django import forms
from .models import Book, Category, Member
from django.contrib.auth.models import User

class BookSearchForm(forms.Form):
    q = forms.CharField(label="Search books (title)", required=False)

class IssueForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.all())
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if current_user and current_user.is_staff:
            self.fields['user'].required = True
            self.fields['user'].queryset = User.objects.filter(is_staff=False).order_by('username')
            self.fields['user'].empty_label = "Select a user to issue book to"

class ReturnForm(forms.Form):
    transaction_id = forms.IntegerField(widget=forms.HiddenInput)

class AddBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['code_no', 'title', 'author', 'category', 'isbn', 'total_copies']
        widgets = {
            'code_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SC(B/M)000001'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def save(self, commit=True):
        book = super().save(commit=False)
        book.available_copies = book.total_copies
        if commit:
            book.save()
        return book

class AddUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    adhaar = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    membership_type = forms.ChoiceField(choices=Member.MEMBERSHIP_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data
