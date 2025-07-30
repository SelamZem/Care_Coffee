from django.shortcuts import render, redirect
from .forms import LoginForm, RegistrationForm
from django.contrib.auth import login


# Create your views here.

def home_view(request):
    return render(request, 'account/home.html')


def login_view(request):
    if request.method=="POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            return redirect('/account/home')
    else:
        form = LoginForm()
    return render(
        request,
        'account/login.html',
        {'form': form}
    )


def register_view(request):
    if request.method=="POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/account/login')
        else:
            return render(request, 'account/registration.html', {'form': form})
        
    # Get request?
    else:
        form = RegistrationForm()
    return render(
        request,
        'account/registration.html', 
        {'form': form}
    )