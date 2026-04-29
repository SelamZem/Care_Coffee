from django.conf import settings
from django.db import models
import base64
from pathlib import Path

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
        default='users/default/default.jpg'
    )

    def __str__(self):
        return f'Profile of {self.user.username}'
    
    def get_photo_base64(self):
        """Return photo as base64 encoded string for embedding in HTML"""
        try:
            if self.photo and self.photo.name != 'users/default/default.jpg':
                # Try static files first (for deployed images)
                static_path = Path(settings.BASE_DIR) / 'static' / self.photo.name
                if static_path.exists():
                    with open(static_path, 'rb') as image_file:
                        encoded = base64.b64encode(image_file.read()).decode('utf-8')
                        if static_path.suffix.lower() in ['.jpg', '.jpeg']:
                            return f'data:image/jpeg;base64,{encoded}'
                        elif static_path.suffix.lower() == '.png':
                            return f'data:image/png;base64,{encoded}'
                        elif static_path.suffix.lower() == '.gif':
                            return f'data:image/gif;base64,{encoded}'
                        else:
                            return f'data:image/jpeg;base64,{encoded}'
                
                # Try media files (for uploaded images)
                media_path = Path(settings.MEDIA_ROOT) / self.photo.name
                if media_path.exists():
                    with open(media_path, 'rb') as image_file:
                        encoded = base64.b64encode(image_file.read()).decode('utf-8')
                        if media_path.suffix.lower() in ['.jpg', '.jpeg']:
                            return f'data:image/jpeg;base64,{encoded}'
                        elif media_path.suffix.lower() == '.png':
                            return f'data:image/png;base64,{encoded}'
                        elif media_path.suffix.lower() == '.gif':
                            return f'data:image/gif;base64,{encoded}'
                        else:
                            return f'data:image/jpeg;base64,{encoded}'
            
            # Return placeholder if no photo or file doesn't exist
            placeholder_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'placeholder.png'
            if placeholder_path.exists():
                with open(placeholder_path, 'rb') as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    return f'data:image/png;base64,{encoded}'
            
            # Final fallback - return empty string
            return ''
        except Exception:
            return ''
