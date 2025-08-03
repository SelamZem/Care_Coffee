from django.shortcuts import render, redirect
from .forms import LoginForm, RegistrationForm, ProfileEditForm
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
        user_form = RegistrationForm(request.POST)
        profile_form= ProfileEditForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user=user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            profile= profile_form.save(commit=False)
            profile.user=user
            profile.save()

            return redirect('/account/login')
        else:
            return render(
                request, 
                'account/registration.html', 
                {'user_form': user_form, 'profile_form':profile_form})
        
    # Get request?
    else:
        user_form = RegistrationForm()
        profile_form = ProfileEditForm()

    return render(
        request,
        'account/registration.html', 
        {'user_form': user_form, 'profile_form':profile_form}
    )