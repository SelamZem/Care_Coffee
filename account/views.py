from django.shortcuts import render, redirect
from .forms import Loginform, RegistrationForm


# Create your views here.

def register_view(request):
    if request.method=="POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
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