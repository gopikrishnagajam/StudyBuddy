from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('dashboard')  # Redirect to dashboard
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'userAuth/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('profile_setup')  # Redirect to profile setup
        else:
            messages.error(request, 'Registration failed. Please check the form.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'userAuth/register.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')  # Redirect to home page after logout

