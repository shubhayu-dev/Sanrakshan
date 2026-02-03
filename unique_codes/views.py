"""
Professional Unique Code views for storage management.

Features:
- Secure Unique Code generation and display
- Code verification and validation
- Print-ready layout
- Scan/Verify tracking and auditing
- Staff-only verification
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
    """Display Unique Code for a storage entry."""
    storage_entry = get_object_or_404(
        StorageEntry, 
        entry_id=entry_id,
        student__user=request.user
    )
    
    # Get or create Unique Code
    qr_code, created = QRCodeImage.objects.get_or_create(
        storage_entry=storage_entry
    )
    
    # Generate code if it doesn't exist
    if not qr_code.code:
        qr_code.generate_qr_image()
    
    # Get storage items for display
    items = storage_entry.get_items_list()
    
    context = {
        'storage_entry': storage_entry,
        'unique_code': qr_code.code, # Pass code instead of image
        'items': items,
        'print_mode': request.GET.get('print', False),
    }
    
    return render(request, 'unique_codes/display.html', context)


@login_required
def generate_qr_code(request, entry_id):
    """Force regenerate Unique Code for a storage entry."""
    storage_entry = get_object_or_404(
        StorageEntry, 
        entry_id=entry_id,
        student__user=request.user
    )
    
    # Get or create Unique Code
    qr_code, created = QRCodeImage.objects.get_or_create(
        storage_entry=storage_entry
    )
    
    # Force regeneration
    qr_code.generate_qr_image(regenerate=True)
    
    messages.success(request, "Unique Code has been regenerated successfully!")
    
    return redirect('unique_codes:display', entry_id=entry_id)


@user_passes_test(is_staff_member)
def verify_code(request):
    """
    Verify a Unique Code provided via search/input.
    This replaces the 'scan' logic.
    """
    code = request.GET.get('code', '').strip()
    
    if not code:
        # If no code, just render the search page (or dashboard)
        # For now, we return a simple error or redirect, but likely this will be called via AJAX 
        # or from the dashboard.
        return JsonResponse({'success': False, 'message': 'No code provided'})

    # Find the QR code object
    try:
        qr_code_obj = QRCodeImage.objects.get(code=code)
        storage_entry = qr_code_obj.storage_entry
    except QRCodeImage.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid Code. Please check and try again.'
        })

    # Check if active
    if not qr_code_obj.is_active:
         return JsonResponse({
            'success': False,
            'message': 'This code has been deactivated (items already claimed)',
            'status': 'deactivated'
        })

    # Record the 'scan' (verification)
    QRScan.objects.create(
        qr_code=qr_code_obj,
        scanned_by=request.user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        is_valid=True,
        action_taken='staff_verification_manual'
    )
    
    # Build response data
    items = list(storage_entry.items.values(
        'item_name', 'category', 'quantity', 'description'
    ))
    
    return JsonResponse({
        'success': True,
        'message': 'Code verified successfully',
        'entry_id': str(storage_entry.entry_id),
        'student_info': {
            'name': storage_entry.student.user.get_full_name(),
            'roll_number': storage_entry.student.roll_number,
            'department': storage_entry.student.get_department_display(),
            'phone': storage_entry.student.phone_number,
        },
        'storage_info': {
            'created_at': storage_entry.created_at.isoformat(),
            'total_items': storage_entry.get_total_items(),
            'description': storage_entry.description,
            'location': storage_entry.storage_location,
            'status': storage_entry.status
        },
        'items': items,
        'can_claim': storage_entry.status == 'active'
    })


@user_passes_test(is_staff_member)
@require_POST
def process_claim(request, entry_id):
    """Process item claim - staff only."""
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
            action_taken='item_claimed_manual',
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Items successfully claimed for {storage_entry.student.user.get_full_name()}. Code deactivated.',
            'claimed_at': storage_entry.claimed_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error claiming items: {str(e)}'
        })


@user_passes_test(is_staff_member)
def bulk_scan_interface(request):
    """
    Hub for staff to enter codes. 
    Renamed conceptually to 'Staff Dashboard' (or part of it).
    """
    recent_scans = QRScan.objects.select_related(
        'qr_code__storage_entry__student__user'
    ).order_by('-scanned_at')[:20]
    
    active_entries_count = StorageEntry.objects.filter(status='active').count()
    
    context = {
        'recent_scans': recent_scans,
        'active_entries_count': active_entries_count,
    }
    
    return render(request, 'unique_codes/bulk_scan.html', context)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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
