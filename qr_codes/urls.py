"""
URL configuration for qr_codes app.
Handles QR code generation and display.
"""

from django.urls import path
from . import views

app_name = 'qr_codes'

urlpatterns = [
    # QR Code generation and display
    path('generate/<uuid:entry_id>/', views.generate_qr_code, name='generate'),
    path('display/<uuid:entry_id>/', views.display_qr_code, name='display'),
    
    # QR Code scanning (staff only)
    path('scan/<uuid:entry_id>/', views.scan_qr_code, name='scan'),
    path('process-claim/<uuid:entry_id>/', views.process_claim, name='process_claim'),
    path('bulk-scan/', views.bulk_scan_interface, name='bulk_scan'),
    
    # API endpoints
    path('api/data/<uuid:entry_id>/', views.get_qr_data, name='api_data'),
    path('webhook/', views.QRWebhookView.as_view(), name='webhook'),
]
