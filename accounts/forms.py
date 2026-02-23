"""
Forms for Accounts App
"""
from django import forms
from django.contrib.auth.models import User
from core.models import Company
from .models import UserProfile


class SignUpForm(forms.Form):
    """
    Custom Sign-Up Form with Company Creation
    """
    # User fields
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Όνομα χρήστη'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Email'
        })
    )
    password1 = forms.CharField(
        label='Κωδικός',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Κωδικός'
        })
    )
    password2 = forms.CharField(
        label='Επιβεβαίωση Κωδικού',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Επιβεβαίωση κωδικού'
        })
    )
    
    # Company fields
    company_name = forms.CharField(
        label='Επωνυμία Εταιρείας',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'π.χ. Μεταφορές Αθηνά ΑΕ'
        })
    )
    company_tax_id = forms.CharField(
        label='ΑΦΜ Εταιρείας',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '999999999'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Οι κωδικοί δεν ταιριάζουν')
        
        return cleaned_data


class AccountProfileForm(forms.ModelForm):
    """
    Form for editing user's own profile (first_name, last_name)
    Email is displayed but not editable
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Όνομα'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Επώνυμο'
            }),
        }
        labels = {
            'first_name': 'Όνομα',
            'last_name': 'Επώνυμο',
        }
