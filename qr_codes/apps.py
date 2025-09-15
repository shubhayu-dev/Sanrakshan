# qr_codes/apps.py
from django.apps import AppConfig

class QrCodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'qr_codes'
    verbose_name = 'QR Code Management'