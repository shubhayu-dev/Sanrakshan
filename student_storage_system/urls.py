"""
Main URL configuration for student_storage_system project.
Professional URL routing with proper namespacing.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # App URLs with namespacing
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),  # Redirect root to login
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('storage/', include('storage.urls', namespace='storage')),
    path('unique-code/', include('unique_codes.urls', namespace='unique_codes')),
]

# Development: Serve media and static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])