from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

class StorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storage'
    verbose_name = 'Storage Management'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import storage.signals
        except ImportError as e:
            raise ImproperlyConfigured(
                "Could not import storage signals. "
                "Make sure storage/signals.py exists and is properly configured."
            ) from e