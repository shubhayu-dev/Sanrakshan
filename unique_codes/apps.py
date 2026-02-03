# qr_codes/apps.py
from django.apps import AppConfig

class UniqueCodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unique_codes'
    verbose_name = 'Unique Code Management'