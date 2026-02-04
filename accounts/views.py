"""
Professional authentication views with security best practices.

Features:
- Custom login/registration with proper validation
- Secure password handling
- User-friendly error messages
- Proper redirects and session management
- Profile management with student data
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from .models import User, StudentProfile, PasswordResetCode
from .forms import (
    CustomUserCreationForm, 
    StudentProfileForm, 
    CustomAuthenticationForm,
    ProfileUpdateForm
)
from storage.models import StorageEntry
from django.core.mail import send_mail
from django.conf import settings


class LandingView(TemplateView):
    """
    Landing page with dual login options and auto-redirect.
    """
    template_name = 'landing.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('storage:staff_dashboard')
            elif hasattr(request.user, 'student_profile'):
                return redirect('storage:dashboard')
            else:
                return redirect('accounts:profile')
        return super().get(request, *args, **kwargs)



class CustomLoginView(LoginView):
    """
    Enhanced login view with custom form and better UX.
    
    Features:
    - Custom authentication form
    - Remember me functionality
    - Proper error handling
    - Clean template integration
    """
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to dashboard after successful login."""
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
            
        user = self.request.user
        if user.is_staff:
            return reverse('storage:staff_dashboard')
        return reverse('storage:dashboard')
    
    def form_valid(self, form):
        """Handle successful login."""
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # Set session to expire when browser closes
            self.request.session.set_expiry(0)
        
        messages.success(
            self.request, 
            f"Welcome back, {form.get_user().get_full_name() or form.get_user().username}!"
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle login errors gracefully."""
        messages.error(
            self.request,
            "Please check your credentials and try again."
        )
        return super().form_invalid(form)


class RegisterView(CreateView):
    """
    Professional registration view with student profile creation.
    
    Features:
    - Combined user + student profile creation
    - Atomic transaction for data consistency
    - Comprehensive validation
    - Auto-login after registration
    """
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('storage:dashboard')
    
    def get_context_data(self, **kwargs):
        """Add student profile form to context."""
        # Ensure object attribute exists for CreateView
        if not hasattr(self, 'object'):
            self.object = None
            
        context = super().get_context_data(**kwargs)
        if 'profile_form' not in context:
            # If we're handling a POST request, initialize with POST data
            if self.request.method == 'POST':
                context['profile_form'] = StudentProfileForm(self.request.POST)
            else:
                context['profile_form'] = StudentProfileForm()
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle both user and profile forms."""
        self.object = None
        form = self.get_form()
        profile_form = StudentProfileForm(request.POST)
        
        if form.is_valid() and profile_form.is_valid():
            return self.form_valid(form, profile_form)
        else:
            return self.form_invalid(form, profile_form)
    
    @transaction.atomic
    def form_valid(self, form, profile_form):
        """Create user and student profile atomically."""
        try:
            # Create user
            user = form.save()
            
            # Create student profile
            student_profile = profile_form.save(commit=False)
            student_profile.user = user
            student_profile.save()
            
            # Auto-login the user
            login(self.request, user)
            
            messages.success(
                self.request,
                f"Welcome to the Storage System, {user.get_full_name()}! "
                f"Your account has been created successfully."
            )
            
            return redirect(self.success_url)
            
        except Exception as e:
            # Log the specific error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            
            # Provide more specific error messages based on the exception type
            error_message = "An error occurred during registration. Please try again."
            if "unique constraint" in str(e).lower():
                if "email" in str(e).lower():
                    error_message = "This email address is already registered."
                elif "username" in str(e).lower():
                    error_message = "This username is already taken."
                elif "roll_number" in str(e).lower():
                    error_message = "This roll number is already registered."
            
            messages.error(self.request, error_message)
            return self.form_invalid(form, profile_form)
    
    def form_invalid(self, form, profile_form=None):
        """Handle validation errors."""
        # If profile_form is None, create it with POST data to preserve user input
        if profile_form is None:
            profile_form = StudentProfileForm(self.request.POST)
        
        context = self.get_context_data(
            form=form,
            profile_form=profile_form
        )
        
        # Collect all errors for better UX
        error_messages = []
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(str(error))
                    else:
                        field_name = form[field].label or field.replace('_', ' ').title()
                        error_messages.append(f"{field_name}: {error}")
        
        if profile_form and profile_form.errors:
            for field, errors in profile_form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(str(error))
                    else:
                        field_name = profile_form[field].label or field.replace('_', ' ').title()
                        error_messages.append(f"{field_name}: {error}")
        
        if error_messages:
            # Show specific errors
            for error_msg in error_messages[:3]:  # Limit to first 3 errors to avoid spam
                messages.error(self.request, error_msg)
        
        return self.render_to_response(context)


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Display user profile with student information.
    
    Features:
    - Complete profile overview
    - Storage statistics
    - Recent activity summary
    """
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        """Add storage statistics to context."""
        context = super().get_context_data(**kwargs)
        
        # Check if staff
        if self.request.user.is_staff:
             # Ideally redirect, but we are in get_context_data. 
             # Better to handle redirect in get/dispatch.
             pass

        try:
            profile = StudentProfile.objects.get(user=self.request.user)
            context['profile'] = profile
            
            # Calculate storage statistics
            storage_entries = profile.storage_entries.all()
            context.update({
                'total_storage_sessions': storage_entries.count(),
                'active_storage_sessions': storage_entries.filter(status='active').count(),
                'claimed_sessions': storage_entries.filter(status='claimed').count(),
                'total_items_stored': sum(entry.get_total_items() for entry in storage_entries),
                'recent_sessions': storage_entries.order_by('-created_at')[:5],
            })
        except StudentProfile.DoesNotExist:
            context['profile'] = None
            
        return context

    def get(self, request, *args, **kwargs):
        # Redirect staff to their dashboard
        if request.user.is_staff:
            return redirect('storage:staff_dashboard')
            
        return super().get(request, *args, **kwargs)


class EditProfileView(LoginRequiredMixin, UpdateView):
    """
    Edit user profile and student information.
    
    Features:
    - Combined user and student profile editing
    - Field validation with custom messages
    - Secure update handling
    """
    form_class = ProfileUpdateForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        """Get current user's student profile."""
        return get_object_or_404(StudentProfile, user=self.request.user)
    
    def get_form_kwargs(self):
        """Pass user instance to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle successful profile update."""
        messages.success(
            self.request,
            "Your profile has been updated successfully!"
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle profile update errors."""
        messages.error(
            self.request,
            "Please correct the errors below and try again."
        )
        return super().form_invalid(form)


@login_required
def storage_history(request):
    """Display complete storage history for the user."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    storage_entries = profile.storage_entries.select_related().prefetch_related('items').order_by('-created_at')
    
    context = {
        'profile': profile,
        'storage_entries': storage_entries,
    }
    
    return render(request, 'accounts/storage_history.html', context)


@login_required
def storage_detail(request, entry_id):
    """Display detailed view of a specific storage entry."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    storage_entry = get_object_or_404(
        StorageEntry, 
        entry_id=entry_id, 
        student=profile
    )
    
    context = {
        'profile': profile,
        'storage_entry': storage_entry,
        'items': storage_entry.items.all(),
    }
    
    return render(request, 'accounts/storage_detail.html', context)


def forgot_password(request):
    """Send password reset code to user's email."""
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        
        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'accounts/forgot_password.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Create reset code
            reset_code = PasswordResetCode.objects.create(
                user=user,
                email=email
            )
            
            # Send email (in development, print to console)
            try:
                send_mail(
                    subject='Password Reset Code - Sanrakshan',
                    message=f'''
Hello {user.get_full_name()},

Your password reset code is: {reset_code.code}

This code will expire in 15 minutes.

If you didn't request this reset, please ignore this email.

Best regards,
Sanrakshan Team
                    '''.strip(),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                messages.success(request, f"Reset code sent to {email}. Check your email and enter the code below.")
                return redirect('accounts:reset_password')
                
            except Exception as e:
                # In development, show the code in messages
                messages.success(request, f"Reset code: {reset_code.code} (Email not configured - use this code)")
                return redirect('accounts:reset_password')
                
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
    
    return render(request, 'accounts/forgot_password.html')


def reset_password(request):
    """Verify code and reset password."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not all([code, new_password, confirm_password]):
            messages.error(request, "Please fill in all fields.")
            return render(request, 'accounts/reset_password.html')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/reset_password.html')
        
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'accounts/reset_password.html')
        
        try:
            reset_code = PasswordResetCode.objects.get(
                code=code,
                is_used=False
            )
            
            if not reset_code.is_valid():
                messages.error(request, "This code has expired. Please request a new one.")
                return redirect('accounts:forgot_password')
            
            # Reset password
            user = reset_code.user
            user.set_password(new_password)
            user.save()
            
            # Mark code as used
            reset_code.mark_used()
            
            messages.success(request, "Password reset successfully! You can now login with your new password.")
            return redirect('accounts:login')
            
        except PasswordResetCode.DoesNotExist:
            messages.error(request, "Invalid reset code.")
    
    return render(request, 'accounts/reset_password.html')


# API Views for AJAX functionality
@login_required
def check_roll_number_availability(request):
    """
    AJAX endpoint to check if roll number is available.
    Used for real-time validation during registration.
    """
    roll_number = request.GET.get('roll_number', '').upper()
    
    if not roll_number:
        return JsonResponse({'available': False, 'message': 'Roll number is required'})
    
    # Check if roll number exists
    exists = StudentProfile.objects.filter(roll_number=roll_number).exists()
    
    return JsonResponse({
        'available': not exists,
        'message': 'Available' if not exists else 'This roll number is already registered'
    })


@login_required
def get_profile_data(request):
    """
    API endpoint to get current user's profile data.
    Used for dynamic content loading.
    """
    try:
        profile = StudentProfile.objects.select_related('user').get(user=request.user)
        
        data = {
            'user': {
                'full_name': profile.user.get_full_name(),
                'email': profile.user.email,
                'username': profile.user.username,
            },
            'profile': {
                'roll_number': profile.roll_number,
                'department': profile.get_department_display(),
                'year': profile.year,
                'phone_number': profile.phone_number,
                'hostel_room': profile.hostel_room,
                'emergency_contact': profile.emergency_contact,
            }
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Student profile not found'
        }, status=404)