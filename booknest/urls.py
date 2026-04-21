from django.contrib import admin
from django.urls import path, include

# 📌 media support (image show করার জন্য)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('library.urls')),
]

# 📸 media files serve (ONLY in development mode)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)