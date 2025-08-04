from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model
from .models import Profile

class LoginForm(forms.Form):
    username_or_email = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        # override clean
        cd = super().clean()
        userInput = cd.get("username_or_email")
        password = cd.get("password")

        if userInput and password:
            try:
                user = User.objects.get(email=userInput)
                username = user.username
            except User.DoesNotExist:
                username = userInput

            user = authenticate(username=username, password=password)

            if not user:
                raise forms.ValidationError("please input valid username/email or password")
            
            self.user = user
        
        else:
            raise forms.ValidationError("Invalid format")
        return cd
    

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    # check password similarity with clean data(it is dictionary)
    def clean_confirm_password(self):
        cd = self.cleaned_data
        password = cd.get("password")
        confirm_password = cd.get("confirm_password")

        if not password or not confirm_password:
            raise forms.ValidationError("Please Enter password for both password and cofirm password")
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Password doesnt match!")
             
        return confirm_password
        
    # check for email uniqness
    def clean_email(self):
        cd = self.cleaned_data
        check_email = cd.get("email")

        if not check_email:
            raise forms.ValidationError("Please input your email")
        if User.objects.filter(email=check_email).exists():
            raise forms.ValidationError("Email already exists")
        
        return check_email

    # check for username uniquness
    def clean_username(self):
        cd = self.cleaned_data
        usernam = cd.get("username")

        if not usernam:
            raise forms.ValidationError("Please Enter username")
        if User.objects.filter(username=usernam).exists():
            raise forms.ValidationError("Username already exists!")

        return usernam

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields=['first_name', 'last_name',"phone_number", "photo"]
        widgets = {
            'photo': forms.FileInput(), 
        }