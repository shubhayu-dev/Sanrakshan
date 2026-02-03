"""
URL configuration for qr_codes app.
Handles Unique Code generation, display, and verification.
"""

from django.urls import path
from . import views

app_name = 'unique_codes'

urlpatterns = [
    # Display unique code (formerly display_qr)
    path('display/<uuid:entry_id>/', views.display_qr_code, name='display'),
    
    # Regenerate code
    path('generate/<uuid:entry_id>/', views.generate_qr_code, name='generate'),
    
    # API endpoint (used by display page)
    path('api/data/<uuid:entry_id>/', views.get_qr_data, name='api_data'),
    
    # Staff verification actions
    path('verify/', views.verify_code, name='verify'), # Replaces scan
    path('process-claim/<uuid:entry_id>/', views.process_claim, name='process_claim'),
    
    # Staff Dashboard / Bulk Scan
    path('bulk-scan/', views.bulk_scan_interface, name='bulk_scan'),
    
    # Webhook
    path('webhook/', views.QRWebhookView.as_view(), name='webhook'),
]
