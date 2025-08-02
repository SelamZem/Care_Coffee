from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialAccount
from .models import Profile
from django.core.files.base import ContentFile
import requests

@receiver(user_logged_in)
def populate_profile_from_google(sender, request, user, **kwargs):
    try:
    
        social_account = SocialAccount.objects.get(user=user)
        extra_data = social_account.extra_data
        picture_url = extra_data.get('picture')

        profile, created = Profile.objects.get_or_create(user=user)

       
        if picture_url and not profile.photo:
            try:
                image_response = requests.get(picture_url)
                if image_response.status_code == 200:
                    profile.photo.save(
                        f"{user.username}_google.jpg",
                        ContentFile(image_response.content),
                        save=True
                    )
            except Exception as e:
                print(f"[Google Profile Image Error] {e}")

    except SocialAccount.DoesNotExist:
        pass 
