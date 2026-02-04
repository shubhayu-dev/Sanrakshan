"""
Professional storage management views.

Features:
- Rich dashboard with statistics and recent activity
- Multi-step item storage process
- Advanced claiming system with validation
- AJAX endpoints for dynamic interactions
- Comprehensive error handling and user feedback
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy
import json
import traceback

from accounts.models import StudentProfile
from .models import StorageEntry, StoredItem
from .forms import StorageEntryForm, StoredItemFormSet, ClaimConfirmationForm


@login_required
def dashboard(request):
    """
    Professional dashboard with comprehensive statistics and recent activity.
    
    Features:
    - Storage statistics with visual indicators
    - Recent activity timeline
    - Quick action buttons
    - Status overview
    """
    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact admin.")
        return redirect('accounts:profile')
    
    # Get storage statistics
    storage_entries = profile.storage_entries.all()
    
    stats = {
        'total_sessions': storage_entries.count(),
        'active_sessions': storage_entries.filter(status='active').count(),
        'claimed_sessions': storage_entries.filter(status='claimed').count(),
        'cancelled_sessions': storage_entries.filter(status='cancelled').count(),
    }
    
    # Calculate total items across all sessions
    total_items = 0
    active_items = 0
    for entry in storage_entries:
        items_count = entry.get_total_items()
        total_items += items_count
        if entry.status == 'active':
            active_items += items_count
    
    stats.update({
        'total_items': total_items,
        'active_items': active_items,
    })
    
    # Recent activity (last 10 entries)
    recent_entries = storage_entries.select_related().prefetch_related('items')[:10]
    
    # Active storage entries for claiming
    active_storage = storage_entries.filter(status='active').prefetch_related('items')
    
    # Storage trends (last 6 months) - SQLite compatible
    from datetime import datetime, timedelta
    six_months_ago = timezone.now() - timedelta(days=180)
    try:
        # Try PostgreSQL syntax first
        monthly_stats = (
            storage_entries
            .filter(created_at__gte=six_months_ago)
            .extra({'month': "date_trunc('month', created_at)"})
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_stats = list(monthly_stats)
    except Exception:
        # Fallback for SQLite - simplified monthly stats
        monthly_stats = []
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            count = storage_entries.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            if count > 0:
                monthly_stats.append({
                    'month': month_start.date(),
                    'count': count
                })
    
    context = {
        'profile': profile,
        'stats': stats,
        'recent_entries': recent_entries,
        'active_storage': active_storage,
        'monthly_stats': monthly_stats,
        'has_active_storage': stats['active_sessions'] > 0,
    }
    
    return render(request, 'storage/dashboard.html', context)


class KeepStuffView(LoginRequiredMixin, CreateView):
    """
    Multi-step storage creation process.
    
    Features:
    - Storage entry with description
    - Dynamic item addition with categories
    - Real-time validation
    - Preview before submission
    """
    model = StorageEntry
    form_class = StorageEntryForm
    template_name = 'storage/keep_stuff.html'
    success_url = reverse_lazy('storage:dashboard')
    
    def get_context_data(self, **kwargs):
        if not hasattr(self, 'object'):
            self.object = None
            
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(StudentProfile, user=self.request.user)
        
        if self.request.POST:
            # Fix: Pass the POST data with the correct prefix
            context['item_formset'] = StoredItemFormSet(
                self.request.POST, 
                prefix='form'  # This ensures formset looks for 'form-0-', 'form-1-', etc.
            )
        else:
            context['item_formset'] = StoredItemFormSet(prefix='form')
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        try:
            with transaction.atomic():
                profile = get_object_or_404(StudentProfile, user=self.request.user)
                
                # Create and save the storage entry first
                storage_entry = form.save(commit=False)
                storage_entry.student = profile
                
                # Set datetime fields if needed
                if not storage_entry.created_at:
                    storage_entry.created_at = timezone.now()
                if not storage_entry.updated_at:
                    storage_entry.updated_at = timezone.now()
                    
                storage_entry.save()
                
                # Now process the items
                items_created = 0
                if item_formset.is_valid():
                    items = item_formset.save(commit=False)
                    for item in items:
                        item.storage_entry = storage_entry
                        item.save()
                        items_created += 1
                else:
                    # Fallback: Create items from POST data
                    total_forms = int(self.request.POST.get('form-TOTAL_FORMS', 0))
                    for i in range(total_forms):
                        item_name = self.request.POST.get(f'form-{i}-item_name')
                        is_deleted = self.request.POST.get(f'form-{i}-DELETE')
                        
                        if item_name and not is_deleted:
                            try:
                                estimated_value = self.request.POST.get(f'form-{i}-estimated_value')
                                estimated_value = float(estimated_value) if estimated_value else 0.0
                                
                                StoredItem.objects.create(
                                    storage_entry=storage_entry,
                                    item_name=item_name,
                                    quantity=int(self.request.POST.get(f'form-{i}-quantity', 1)),
                                    category=self.request.POST.get(f'form-{i}-category', ''),
                                    description=self.request.POST.get(f'form-{i}-description', ''),
                                    estimated_value=estimated_value
                                )
                                items_created += 1
                            except (ValueError, TypeError):
                                continue
                
                # Check if any items were created
                if items_created == 0:
                    storage_entry.delete()
                    messages.error(self.request, "Please add at least one item to store.")
                    return self.form_invalid(form)
                
                # Generate QR code
                try:
                    storage_entry.generate_qr_data()
                    storage_entry.save()
                except Exception:
                    # Don't fail if QR generation fails
                    pass
                
                messages.success(self.request, f"Storage entry created successfully with {items_created} item(s)!")
                return redirect('qr_codes:display', entry_id=storage_entry.entry_id)
                
        except Exception as e:
            messages.error(self.request, f"Error creating storage entry: {str(e)}")
            return self.form_invalid(form)

@login_required
def claim_stuff(request):
    """
    Advanced claiming interface with confirmation and validation.
    
    Features:
    - List of claimable storage entries
    - Item-by-item claiming (future feature)
    - Confirmation workflow
    - Audit trail
    """
    # Get the profile FIRST before using it
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # DEBUG: Check what we have (now profile is available)
    print(f"=== CLAIM DEBUG ===")
    print(f"User: {request.user}")
    print(f"Profile: {profile}")
    
    # Check ALL entries first
    all_entries = profile.storage_entries.all()
    print(f"Total entries for user: {all_entries.count()}")
    
    for entry in all_entries:
        print(f"Entry {entry.entry_id}: status='{entry.status}', items={entry.get_total_items()}")
    
    # Get active storage entries
    active_entries = (
        profile.storage_entries
        .filter(status='active')
        .prefetch_related('items')
        .order_by('-created_at')
    )
    
    # DEBUG: Check active entries specifically
    print(f"Active entries count: {active_entries.count()}")
    print(f"Active entries exist: {active_entries.exists()}")
    for entry in active_entries:
        print(f"Active Entry: {entry.entry_id}, items: {entry.get_total_items()}")
    
    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        if entry_id:
            return claim_storage_entry_view(request, entry_id)
    
    context = {
        'profile': profile,
        'storage_sessions': active_entries,  # Changed to match template
        'active_entries': active_entries,    # Keep both for compatibility
        'has_active_storage': active_entries.exists(),
    }
    
    # DEBUG: Check context
    print(f"Context has_active_storage: {context['has_active_storage']}")
    print(f"Context storage_sessions count: {context['storage_sessions'].count()}")
    
    return render(request, 'storage/claim_stuff.html', context)

@login_required
def claim_storage_entry_view(request, entry_id):
    """
    Individual storage entry claiming with confirmation.
    
    Features:
    - Entry details display
    - Confirmation workflow
    - Immediate claiming or scheduled pickup
    """
    profile = get_object_or_404(StudentProfile, user=request.user)
    storage_entry = get_object_or_404(
        StorageEntry, 
        entry_id=entry_id,
        student=profile,
        status='active'
    )
    
    if request.method == 'POST':
        form = ClaimConfirmationForm(request.POST)
        if form.is_valid():
            try:
                # Claim the storage entry
                storage_entry.claim_items(claimed_by=request.user)
                
                # Ensure claimed_at is set
                if not storage_entry.claimed_at:
                    storage_entry.claimed_at = timezone.now()
                    storage_entry.save()
                
                confirmation_notes = form.cleaned_data.get('confirmation_notes', '')
                if confirmation_notes:
                    storage_entry.staff_notes = f"{storage_entry.staff_notes}\nStudent notes: {confirmation_notes}"
                    storage_entry.save()
                
                messages.success(
                    request,
                    f"Storage entry claimed successfully! "
                    f"Please collect your {storage_entry.get_total_items()} item(s) from the storage facility."
                )
                
                return redirect('storage:dashboard')
                
            except Exception as e:
                print(f"Error claiming storage entry: {str(e)}")
                traceback.print_exc()
                messages.error(request, "An error occurred while claiming your items. Please try again.")
                
    else:
        form = ClaimConfirmationForm()
    
    context = {
        'profile': profile,
        'storage_entry': storage_entry,
        'items': storage_entry.get_items_list(),
        'form': form,
    }
    
    return render(request, 'storage/claim_confirm.html', context)


class StorageHistoryView(LoginRequiredMixin, ListView):
    """
    Complete storage history with filtering and pagination.
    
    Features:
    - Paginated history
    - Status filtering
    - Date range filtering
    - Export functionality
    """
    model = StorageEntry
    template_name = 'storage/history.html'
    context_object_name = 'entries'
    paginate_by = 10
    
    def get_queryset(self):
        profile = get_object_or_404(StudentProfile, user=self.request.user)
        queryset = profile.storage_entries.prefetch_related('items').order_by('-created_at')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        if not hasattr(self, 'object'):
            self.object = None
            
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(StudentProfile, user=self.request.user)
        
        if self.request.POST:
            # For POST requests, pass instance=None explicitly
            context['item_formset'] = StoredItemFormSet(
                self.request.POST, 
                instance=None,  # This is the key fix
                prefix='form'
            )
        else:
            # For GET requests, also pass instance=None
            context['item_formset'] = StoredItemFormSet(
                instance=None,  # This is the key fix
                prefix='form'
            )
        
        return context


# AJAX API Endpoints

@login_required
def get_student_items(request):
    """
    API endpoint to get student's storage items.
    Used for dynamic content loading and autocomplete.
    """
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Get unique item names for autocomplete
    unique_items = (
        StoredItem.objects
        .filter(storage_entry__student=profile)
        .values_list('item_name', flat=True)
        .distinct()
        .order_by('item_name')
    )
    
    return JsonResponse({
        'success': True,
        'items': list(unique_items),
        'total_unique_items': len(unique_items)
    })


@login_required
def claim_storage_entry(request, entry_id):
    """
    AJAX endpoint for quick claiming.
    Used for one-click claiming from dashboard.
    
    Fixed: Handle None claimed_at values to prevent isoformat errors.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    try:
        storage_entry = StorageEntry.objects.get(
            entry_id=entry_id,
            student=profile,
            status='active'
        )
        
        # Claim the items
        storage_entry.claim_items(claimed_by=request.user)
        
        # Ensure claimed_at is set (fix for isoformat error)
        if not storage_entry.claimed_at:
            storage_entry.claimed_at = timezone.now()
            storage_entry.save()
        
        # Safely handle claimed_at for JSON response
        claimed_at_iso = storage_entry.claimed_at.isoformat() if storage_entry.claimed_at else timezone.now().isoformat()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully claimed {storage_entry.get_total_items()} item(s)!',
            'claimed_at': claimed_at_iso,
            'entry_id': storage_entry.entry_id,
            'status': storage_entry.status,
        })
        
    except StorageEntry.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Storage entry not found or already claimed.'
        })
    except Exception as e:
        print(f"Error in claim_storage_entry AJAX: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while claiming items. Please try again.'
        })


@login_required
def get_storage_stats(request):
    """
    API endpoint for real-time dashboard statistics.
    Used for dynamic dashboard updates.
    """
    try:
        profile = get_object_or_404(StudentProfile, user=request.user)
        storage_entries = profile.storage_entries.all()
        
        stats = {
            'total_sessions': storage_entries.count(),
            'active_sessions': storage_entries.filter(status='active').count(),
            'claimed_sessions': storage_entries.filter(status='claimed').count(),
            'total_items': sum(entry.get_total_items() for entry in storage_entries),
            'last_updated': timezone.now().isoformat(),
        }
        
        return JsonResponse({'success': True, 'stats': stats})
    
    except Exception as e:
        print(f"Error in get_storage_stats: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error retrieving statistics'
        })