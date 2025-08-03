from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_username

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data

        email = extra_data.get('email', '')
        first_name = extra_data.get('given_name', '')
        last_name = extra_data.get('family_name', '')
        full_name = extra_data.get('name', '')

        user.email = email or user.email
        user.first_name = first_name
        user.last_name = last_name

        if not user.username:
            base_username = full_name.lower().replace(" ", "") if full_name else email.split('@')[0]
            user_username(user, base_username)

        user.set_unusable_password()
        user.save()
        return user
