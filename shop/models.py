from django.db import models
import base64
from pathlib import Path
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name= models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'])
        ]
        verbose_name = "category"
        verbose_name_plural="categories"
        
    def __str__(self):
        return self.name
    
class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='products/%Y/%m/%d',
        blank=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available=models.BooleanField(default=True)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)

    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created'])
        ]


    def __str__(self):
        return self.name
    
    def get_image_base64(self):
        """Return image as base64 encoded string for embedding in HTML"""
        try:
            if self.image and self.image.name:
                # Try static files first (for deployed images)
                static_path = Path(settings.BASE_DIR) / 'static' / self.image.name
                if static_path.exists():
                    with open(static_path, 'rb') as image_file:
                        encoded = base64.b64encode(image_file.read()).decode('utf-8')
                        if static_path.suffix.lower() in ['.jpg', '.jpeg']:
                            return f'data:image/jpeg;base64,{encoded}'
                        elif static_path.suffix.lower() == '.png':
                            return f'data:image/png;base64,{encoded}'
                        elif static_path.suffix.lower() == '.gif':
                            return f'data:image/gif;base64,{encoded}'
                        elif static_path.suffix.lower() == '.webp':
                            return f'data:image/webp;base64,{encoded}'
                        else:
                            return f'data:image/jpeg;base64,{encoded}'
                
                # Try media files (for uploaded images)
                media_path = Path(settings.MEDIA_ROOT) / self.image.name
                if media_path.exists():
                    with open(media_path, 'rb') as image_file:
                        encoded = base64.b64encode(image_file.read()).decode('utf-8')
                        if media_path.suffix.lower() in ['.jpg', '.jpeg']:
                            return f'data:image/jpeg;base64,{encoded}'
                        elif media_path.suffix.lower() == '.png':
                            return f'data:image/png;base64,{encoded}'
                        elif media_path.suffix.lower() == '.gif':
                            return f'data:image/gif;base64,{encoded}'
                        elif media_path.suffix.lower() == '.webp':
                            return f'data:image/webp;base64,{encoded}'
                        else:
                            return f'data:image/jpeg;base64,{encoded}'
            
            # Return placeholder if no image or file doesn't exist
            placeholder_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'placeholder.png'
            if placeholder_path.exists():
                with open(placeholder_path, 'rb') as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    return f'data:image/png;base64,{encoded}'
            
            # Final fallback - return empty string
            return ''
        except Exception:
            return ''