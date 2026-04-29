from django.http import HttpResponse, Http404
from django.conf import settings
import os
from pathlib import Path
import mimetypes

class MediaServeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/media/'):
            try:
                # Remove /media/ prefix to get the file path
                file_path = request.path[7:]  # Remove '/media/'
                full_path = settings.MEDIA_ROOT / file_path
                
                if full_path.exists() and full_path.is_file():
                    # Determine content type
                    content_type, _ = mimetypes.guess_type(str(full_path))
                    if content_type is None:
                        content_type = 'application/octet-stream'
                    
                    # Read and serve the file
                    with open(full_path, 'rb') as f:
                        response = HttpResponse(f.read(), content_type=content_type)
                        response['Content-Disposition'] = f'inline; filename="{full_path.name}"'
                        return response
                else:
                    raise Http404("Media file not found")
            except Exception as e:
                raise Http404(f"Error serving media file: {e}")
        
        response = self.get_response(request)
        return response
