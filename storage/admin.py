from django.contrib import admin
from django.utils.html import format_html
from .models import StorageEntry, StoredItem


@admin.register(StorageEntry)
class StorageEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_id_short', 'get_student_info', 'get_status_badge', 'get_total_items', 'created_at']
    list_filter = ['status', 'created_at', 'student__department', 'student__year']
    search_fields = ['entry_id', 'student__roll_number', 'student__user__first_name', 'student__user__last_name']
    readonly_fields = ['entry_id', 'created_at', 'updated_at']
    
    def entry_id_short(self, obj):
        return str(obj.entry_id)[:8] + '...'
    entry_id_short.short_description = 'Entry ID'
    
    def get_student_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.student.user.get_full_name(),
            obj.student.roll_number
        )
    get_student_info.short_description = 'Student'
    
    def get_status_badge(self, obj):
        colors = {'active': 'success', 'claimed': 'secondary', 'expired': 'warning'}
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.status, 'primary'),
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'


@admin.register(StoredItem)
class StoredItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'get_storage_entry', 'category', 'quantity', 'get_student']
    list_filter = ['category', 'storage_entry__status']
    search_fields = ['item_name', 'description', 'storage_entry__student__roll_number']
    
    def get_storage_entry(self, obj):
        return str(obj.storage_entry.entry_id)[:8] + '...'
    get_storage_entry.short_description = 'Storage Entry'
    
    def get_student(self, obj):
        return obj.storage_entry.student.user.get_full_name()
    get_student.short_description = 'Student'
