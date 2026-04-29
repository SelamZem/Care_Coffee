"""
URL configuration for care_coffee project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import HttpResponse, Http404
from pathlib import Path
import mimetypes


def serve_media(request, path):
    try:
        # Try to serve from media directory first
        file_path = Path(settings.MEDIA_ROOT) / path
        
        # If not in media, try staticfiles/media (for copied files)
        if not file_path.exists():
            staticfiles_media = Path(settings.STATIC_ROOT) / 'media' / path
            if staticfiles_media.exists():
                file_path = staticfiles_media
        
        # If still not found, try to serve placeholder for images
        if not file_path.exists():
            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                # Serve placeholder image
                placeholder_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'placeholder.png'
                if placeholder_path.exists():
                    file_path = placeholder_path
        
        if file_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            response = HttpResponse(file_path.open('rb').read(), content_type=mime_type)
            response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
            return response
        else:
            # Return empty response with proper headers instead of 404
            return HttpResponse('', status=200, content_type='text/plain')
    except Exception as e:
        # Return empty response on error
        return HttpResponse('', status=200, content_type='text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('allauth.urls')), 

    path('account/', include('useraccount.urls', namespace="account")), 
    path('cart/', include('cart.urls', namespace='cart')),
    path('order/', include('order.urls', namespace='order')),
    path('shop/', include('shop.urls', namespace='shop') ),
    

    path('', lambda request: redirect('shop/', permanent=False)),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve media files through a custom view
    urlpatterns += [
        path('media/<path:path>', serve_media, name='serve_media'),
    ]