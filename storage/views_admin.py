from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q
from django.utils import timezone
from .models import StorageEntry
from unique_codes.models import UniqueCodeScan
import datetime

class StaffDashboardView(UserPassesTestMixin, TemplateView):
    template_name = 'storage/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date ranges
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Statistics
        context['stats'] = {
            'total_active': StorageEntry.objects.filter(status='active').count(),
            'total_claimed': StorageEntry.objects.filter(status='claimed').count(),
            'today_entries': StorageEntry.objects.filter(created_at__gte=today_start).count(),
            'today_claims': StorageEntry.objects.filter(claimed_at__gte=today_start).count(),
        }
        
        # Recent Activity (Combined storage and claims)
        # This is a bit complex to interleave efficiently in Django without a union, 
        # so we'll just show recent Entries and recent Claims separately or just Entries sorted by update
        
        context['recent_entries'] = StorageEntry.objects.select_related(
            'student__user'
        ).order_by('-updated_at')[:10]
        
        # Recent Scans/Verifications
        context['recent_scans'] = UniqueCodeScan.objects.select_related(
            'unique_code__storage_entry__student__user',
            'scanned_by'
        ).order_by('-scanned_at')[:10]
        
        return context
