"""
Professional QR code views for storage management.

Features:
- Secure QR code generation and display
- QR code scanning with validation
- Print-ready QR code layout
- Scan tracking and auditing
- Staff-only QR verification
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from storage.models import StorageEntry
from accounts.models import StudentProfile
from .models import QRCodeImage, QRScan
import json
import ast
from django.views.generic import View
from django.utils.decorators import method_decorator


def is_staff_member(user):
    """Check if user is staff member for staff-only views."""
    return user.is_authenticated and user.is_staff


@login_required
def display_qr_code(request, entry_id):
    """Display QR code for a storage entry with print-ready layout."""
    storage_entry = get_object_or_404(
        StorageEntry, 
        entry_id=entry_id,
        student__user=request.user
    )
    
    # Get or create QR code image
    qr_code, created = QRCodeImage.objects.get_or_create(
        storage_entry=storage_entry
    )
    
    # Generate image if it doesn't exist
    if not qr_code.image:
        qr_code.generate_qr_image()
    
    # Get storage items for display
    items = storage_entry.get_items_list()
    
    context = {
        'storage_entry': storage_entry,
        'qr_code': qr_code,
        'items': items,
        'print_mode': request.GET.get('print', False),
        'qr_scan_url': request.build_absolute_uri(
            reverse('qr_codes:scan', kwargs={'entry_id': entry_id})
        ),
    }
    
    return render(request, 'qr_codes/display.html', context)


@login_required
def generate_qr_code(request, entry_id):
    """Force regenerate QR code for a storage entry."""
    storage_entry = get_object_or_404(
        StorageEntry, 
        entry_id=entry_id,
        student__user=request.user
    )
    
    # Get or create QR code
    qr_code, created = QRCodeImage.objects.get_or_create(
        storage_entry=storage_entry
    )
    
    # Force regeneration
    qr_code.generate_qr_image(regenerate=True)
    
    messages.success(request, "QR code has been regenerated successfully!")
    
    return redirect('qr_codes:display', entry_id=entry_id)


@user_passes_test(is_staff_member)
def scan_qr_code(request, entry_id):
    """Scan and validate QR code - staff only view."""
    storage_entry = get_object_or_404(StorageEntry, entry_id=entry_id)
    
    # Check if QR code is active
    try:
        qr_code = storage_entry.qr_code
        if not qr_code.is_active:
            return JsonResponse({
                'success': False,
                'message': 'This QR code has been deactivated (items already claimed)',
                'status': 'deactivated'
            })
    except:
        pass
    
    # Only active entries can be processed
    if storage_entry.status != 'active':
        return JsonResponse({
            'success': False,
            'message': f'This storage entry is {storage_entry.get_status_display().lower()}',
            'status': storage_entry.status
        })
    
    if request.method == 'POST':
        # Process QR scan
        try:
            qr_code = storage_entry.qr_code
            
            # Record the scan
            scan = QRScan.objects.create(
                qr_code=qr_code,
                scanned_by=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                is_valid=True,
                action_taken='staff_verification'
            )
            
            # Get storage items
            items = list(storage_entry.items.values(
                'item_name', 'category', 'quantity', 'description'
            ))
            
            return JsonResponse({
                'success': True,
                'message': 'QR code is valid',
                'student_info': {
                    'name': storage_entry.student.user.get_full_name(),
                    'roll_number': storage_entry.student.roll_number,
                    'department': storage_entry.student.get_department_display(),
                    'phone': storage_entry.student.phone_number,
                },
                'storage_info': {
                    'entry_id': str(storage_entry.entry_id),
                    'created_at': storage_entry.created_at.isoformat(),
                    'total_items': storage_entry.get_total_items(),
                    'description': storage_entry.description,
                    'location': storage_entry.storage_location,
                },
                'items': items,
                'can_claim': True
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing QR code: {str(e)}'
            })
    
    # GET request - show scan interface
    context = {
        'storage_entry': storage_entry,
        'can_process': storage_entry.status == 'active'
    }
    
    return render(request, 'qr_codes/scan.html', context)


@user_passes_test(is_staff_member)
@require_POST
def process_claim(request, entry_id):
    """Process item claim after QR validation - staff only."""
    storage_entry = get_object_or_404(StorageEntry, entry_id=entry_id)
    
    if storage_entry.status != 'active':
        return JsonResponse({
            'success': False,
            'message': 'This storage entry cannot be claimed'
        })
    
    try:
        # Get any additional notes
        notes = request.POST.get('notes', '')
        
        # Claim the items (this will also deactivate the QR code)
        storage_entry.claim_items(claimed_by=request.user)
        
        # Add notes if provided
        if notes:
            storage_entry.staff_notes += f"\nClaim notes: {notes}"
            storage_entry.save()
        
        # Record the scan with claim action
        qr_code = storage_entry.qr_code
        QRScan.objects.create(
            qr_code=qr_code,
            scanned_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_valid=True,
            action_taken='item_claimed',
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Items successfully claimed for {storage_entry.student.user.get_full_name()}. QR code has been deactivated.',
            'claimed_at': storage_entry.claimed_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error claiming items: {str(e)}'
        })


@login_required
def get_qr_data(request, entry_id):
    """API endpoint to get QR code data."""
    storage_entry = get_object_or_404(
        StorageEntry, 
        entry_id=entry_id
    )
    
    # Check permissions - students can only see their own
    if not request.user.is_staff and storage_entry.student.user != request.user:
        raise Http404
    
    try:
        qr_code = storage_entry.qr_code
        
        # If QR code is claimed, return limited information
        if storage_entry.status == 'claimed':
            return JsonResponse({
                'success': False,
                'message': 'This QR code has been deactivated - items were already claimed',
                'status': 'claimed',
                'claimed_info': {
                    'claimed_at': storage_entry.claimed_at.isoformat() if storage_entry.claimed_at else None,
                    'claimed_by': storage_entry.claimed_by.get_full_name() if storage_entry.claimed_by else 'Staff',
                    'student_name': storage_entry.student.user.get_full_name(),
                    'roll_number': storage_entry.student.roll_number,
                }
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'entry_id': str(storage_entry.entry_id),
                'student_name': storage_entry.student.user.get_full_name(),
                'roll_number': storage_entry.student.roll_number,
                'department': storage_entry.student.get_department_display(),
                'phone': storage_entry.student.phone_number,
                'status': storage_entry.status,
                'created_at': storage_entry.created_at.isoformat(),
                'total_items': storage_entry.get_total_items(),
                'qr_active': qr_code.is_active,
                'items': list(storage_entry.items.values('item_name', 'quantity', 'category'))
            }
        })
        
    except QRCodeImage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'QR code not found'
        })


@user_passes_test(is_staff_member)
def bulk_scan_interface(request):
    """Staff interface for bulk QR code scanning."""
    recent_scans = QRScan.objects.select_related(
        'qr_code__storage_entry__student__user'
    ).order_by('-scanned_at')[:20]
    
    active_entries_count = StorageEntry.objects.filter(status='active').count()
    
    context = {
        'recent_scans': recent_scans,
        'active_entries_count': active_entries_count,
    }
    
    return render(request, 'qr_codes/bulk_scan.html', context)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@method_decorator(csrf_exempt, name='dispatch')
class QRWebhookView(View):
    """Webhook view for external QR scanner apps."""
    
    def post(self, request, *args, **kwargs):
        """Handle webhook from QR scanner apps."""
        try:
            data = json.loads(request.body)
            qr_data = data.get('qr_data')
            
            # Parse QR data
            if qr_data:
                # Try to extract entry_id from QR data
                qr_content = ast.literal_eval(qr_data) if isinstance(qr_data, str) else qr_data
                entry_id = qr_content.get('entry_id')
                
                if entry_id:
                    storage_entry = StorageEntry.objects.get(entry_id=entry_id)
                    
                    # Record the scan
                    QRScan.objects.create(
                        qr_code=storage_entry.qr_code,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_valid=True,
                        action_taken='webhook_scan',
                        notes='Scanned via external app'
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'QR code valid',
                        'entry_id': str(storage_entry.entry_id),
                        'status': storage_entry.status
                    })
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid QR data'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
