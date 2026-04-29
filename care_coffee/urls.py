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
    file_path = Path(settings.MEDIA_ROOT) / path
    if file_path.is_file():
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return HttpResponse(file_path.open('rb').read(), content_type=mime_type)
    else:
        raise Http404


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