from email.policy import default
from django.conf import settings
from django.db import models

class Profile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(
        upload_to='users/%Y/%m/%d/',
        blank=True,
        default = 'default/default.jpg'
    )

    def __str__(self):
        return f'Profile of {self.user.username}'
