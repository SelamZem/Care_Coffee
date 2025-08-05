from django.shortcuts import render, redirect, get_object_or_404
from .forms import LoginForm, RegistrationForm, ProfileEditForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages

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

def logout_view(request):
    logout(request)
    return redirect('account:login')

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

            send_welcome_email(user)
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

@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method=="POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail')
        
    else:
        form= ProfileEditForm(instance=profile)

    return render(request,
                  'account/edit_profile.html',
                  {'form':form})


# this is not implemented yet...created just to test

@login_required
def profile_detail(request):
    return render(request, 'useraccount/profile_detail.html', {'profile': request.user.profile})


def request_password_reset(request):
    if request.method=="POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            send_reset_email(user)
            messages.success(request, "please check your email")
    return render(request,
                'account/request_password_reset.html')
def reset_password(request,user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':

        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password updated successfully.")
            return redirect('account:login') 

    return render(request, 'account/reset_password.html', {'user': user})


@login_required
def update_password(request):
    user = request.user

    if request.method=="POST":
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not user.check_password(old_password):
            messages.error(request,"please input the correct password")
        elif new_password!=confirm_password:
            messages.error(request,"The password doesnt match")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password updated successfully.")
            return redirect('account:home')
        
    return render(request,
                  'account/update_password.html',
                  {'user':user})


def send_welcome_email(user):
    subject="Welcome to Care Coffee"
    message = f"Hi, {user.profile.first_name}, \n Thanks for joining us!!"
    from_email = "carecoffee@gmail.com"
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)

def send_reset_email(user):
    reset_link = f"http://127.0.0.1:8000/account/reset-password/{user.id}/"
    subject = "Reset your password"
    message = f"Hi {user.profile.first_name},\n\nClick this link to reset your password:\n{reset_link}\n\nIf you didn't request this, just ignore this email."
    send_mail(subject, message, 'carecoffee@gmail.com', [user.email])