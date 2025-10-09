from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve
from dotenv import load_dotenv
load_dotenv()
import os


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('fiverr.urls')),
    path('', include('freelancerr.urls')),
]

SERVE_MEDIA = os.getenv("SERVE_MEDIA", "False").strip().lower() in ("true","1","yes")

if SERVE_MEDIA:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', static_serve, {'document_root': settings.STATIC_ROOT}),
    ]
