from django import forms
from django.contrib.auth.models import User

class Loginform(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="password",widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="confirm password",widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email','password', 'first_name', 'last_name']

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
        username = cd.get("username")

        if not username:
            raise forms.ValidationError("Please Enter username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists!")

        return username

    # saves automaticaly since commit=True
    def save(self, commit=True):
        cd = self.cleaned_data
        user = super().save(commit=False)
        user.set_password(cd.get("password"))
        if commit:
            user.save()
        return user
        
