"""
URL configuration for storage app.
Handles dashboard and storage-related functionality.
"""

from django.urls import path
from . import views
from . import views_admin

app_name = 'storage'

urlpatterns = [
    # Dashboard - main hub for students
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Storage actions
    path('keep/', views.KeepStuffView.as_view(), name='keep_stuff'),
    path('claim/', views.claim_stuff, name='claim_stuff'),
    
    # Staff/Admin Views
    path('staff/dashboard/', views_admin.StaffDashboardView.as_view(), name='staff_dashboard'),

    # AJAX endpoints (we'll add these later)
    path('api/items/', views.get_student_items, name='api_items'),
    path('api/claim/<uuid:entry_id>/', views.claim_storage_entry, name='api_claim'),
]