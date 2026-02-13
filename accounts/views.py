"""
Authentication Views for GreekFleet 360
Login, Logout, and SaaS Sign-Up
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.views import View
from django import forms
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


class SignUpView(View):
    """
    SaaS Sign-Up View
    Creates User, Company, and UserProfile
    """
    def get(self, request):
        form = SignUpForm()
        return render(request, 'accounts/signup.html', {'form': form})
    
    def post(self, request):
        form = SignUpForm(request.POST)
        
        if form.is_valid():
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            
            # Create Company
            company = Company.objects.create(
                name=form.cleaned_data['company_name'],
                tax_id=form.cleaned_data['company_tax_id'],
                business_type='MIXED',
                is_active=True
            )
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                company=company,
                role='ADMIN'  # First user is admin
            )
            
            # Log the user in automatically
            login(request, user)
            
            return redirect('web:dashboard')
        
        return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """
    Login View
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('web:dashboard')
    else:
        form = AuthenticationForm()
    
    # Apply Tailwind classes to form fields
    for field in form.fields.values():
        field.widget.attrs['class'] = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Logout View
    """
    logout(request)
    return redirect('accounts:login')
