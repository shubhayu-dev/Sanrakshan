"""
Professional Django Admin configuration for QR codes.

Features:
- QR code image management with preview
- Scan tracking and analytics
- Bulk operations for QR regeneration
- Security monitoring dashboard
- Export functionality
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
import csv

from .models import UniqueCode, UniqueCodeScan


@admin.register(UniqueCode)
class UniqueCodeAdmin(admin.ModelAdmin):
    """Professional Unique Code management."""
    
    list_display = [
        'get_student_info', 'get_code_preview', 'is_active', 
        'generated_at', 'get_scan_count', 'get_storage_status'
    ]
    
    list_filter = [
        'is_active', 'generated_at',
    ]
    
    search_fields = [
        'storage_entry__student__roll_number',
        'storage_entry__student__user__first_name',
        'storage_entry__student__user__last_name',
        'uuid',
        'code',
    ]
    
    readonly_fields = [
        'uuid', 'generated_at', 'get_code_preview_large', 
        'get_storage_details', 'get_scan_summary', 'content_data'
    ]
    
    actions = ['regenerate_codes']
    
    def get_student_info(self, obj):
        """Display student information."""
        student = obj.storage_entry.student
        return format_html(
            '<strong>{}</strong><br><small>{} - {}</small>',
            student.user.get_full_name(),
            student.roll_number,
            student.get_department_display()
        )
    get_student_info.short_description = 'Student'
    
    def get_code_preview(self, obj):
        """Display small Code preview."""
        if obj.code:
            return format_html(
                '<span style="font-family: monospace; font-weight: bold;">{}</span>',
                obj.code
            )
        return "No code"
    get_code_preview.short_description = 'Code'
    
    def get_scan_count(self, obj):
        """Display scan count."""
        count = obj.scans.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    get_scan_count.short_description = 'Scans'
    
    def get_storage_status(self, obj):
        """Display storage entry status."""
        status = obj.storage_entry.status
        colors = {
            'active': '#f39c12',
            'claimed': '#27ae60',
            'expired': '#e74c3c',
            'cancelled': '#95a5a6'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(status, '#6c757d'),
            obj.storage_entry.get_status_display().upper()
        )
    get_storage_status.short_description = 'Status'
    
    def get_code_preview_large(self, obj):
        """Display large Unique Code preview."""
        if obj.code:
            return format_html(
                '<div style="text-align: center; background: #f8f9fa; padding: 20px; border-radius: 8px;">'
                '<div style="font-family: monospace; font-size: 24px; font-weight: bold; letter-spacing: 2px;">{}</div>'
                '</div>',
                obj.code
            )
        return "No code generated"
    get_code_preview_large.short_description = 'Preview'
    
    def get_storage_details(self, obj):
        """Display storage information."""
        entry = obj.storage_entry
        return format_html(
            'Entry ID: {}<br>Created: {}<br>Status: {}<br>Items: {}',
            entry.entry_id,
            entry.created_at.strftime('%b %d, %Y'),
            entry.get_status_display(),
            entry.get_total_items()
        )
    get_storage_details.short_description = 'Storage Info'
    
    def get_scan_summary(self, obj):
        """Display scan summary."""
        count = obj.scans.count()
        if count == 0:
            return "No scans yet"
        last_scan = obj.scans.order_by('-scanned_at').first()
        return format_html(
            '{} total scans<br>Last: {}',
            count,
            last_scan.scanned_at.strftime('%b %d, %Y') if last_scan else 'Never'
        )
    get_scan_summary.short_description = 'Scan History'
    
    def regenerate_codes(self, request, queryset):
        """Bulk regenerate Unique codes."""
        count = 0
        for code_obj in queryset:
            try:
                code_obj.generate_code_string(regenerate=True)
                count += 1
            except Exception as e:
                messages.error(request, f'Failed to regenerate: {str(e)}')
        messages.success(request, f'Regenerated {count} codes.')
    regenerate_codes.short_description = "Regenerate Codes"


@admin.register(UniqueCodeScan)
class UniqueCodeScanAdmin(admin.ModelAdmin):
    """Scan tracking."""
    
    list_display = [
        'get_code_info', 'scanned_by', 'scanned_at', 
        'action_taken', 'is_valid', 'ip_address'
    ]
    
    list_filter = [
        'is_valid', 'action_taken', 'scanned_at',
    ]
    
    search_fields = [
        'unique_code__storage_entry__student__roll_number',
        'scanned_by__username',
        'ip_address'
    ]
    
    date_hierarchy = 'scanned_at'
    ordering = ['-scanned_at']
    
    def get_code_info(self, obj):
        """Display Code info."""
        student = obj.unique_code.storage_entry.student
        return format_html(
            '{} ({})',
            student.user.get_full_name(),
            student.roll_number
        )
    get_code_info.short_description = 'Student'
