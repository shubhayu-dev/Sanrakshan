"""
Professional Django forms with comprehensive validation.

Features:
- Custom user creation with student profile
- Enhanced authentication form
- Rich validation with helpful error messages
- Bootstrap-ready styling
- Security best practices

CUSTOMIZATION GUIDE FOR OTHER COLLEGES:
1. Update EMAIL_DOMAIN in CustomUserCreationForm.clean_email()
2. Modify roll number validation in StudentProfileForm.clean_roll_number()
3. Update placeholders and help texts as needed
4. Adjust department choices in models.py
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.html import format_html
import re

from .models import User, StudentProfile


class CustomAuthenticationForm(AuthenticationForm):
    """
    Enhanced login form with better UX and validation.
    
    Features:
    - Email or username login
    - Remember me functionality
    - Better error messages
    - Bootstrap styling
    
    CUSTOMIZATION: No changes needed for most colleges
    """
    
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email or Username',
            'autocomplete': 'username',
            'autofocus': True,
        }),
        label="Email or Username"
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        }),
        label="Password"
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label="Remember me"
    )
    
    def clean_username(self):
        """Allow login with email or username."""
        username = self.cleaned_data.get('username')
        
        if '@' in username:
            # Try to find user by email
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        
        return username
    
    def clean(self):
        """Enhanced authentication with better error messages."""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username is not None and password:
            self.user_cache = authenticate(
                self.request, 
                username=username, 
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError(
                    "Invalid email/username or password. Please check your credentials.",
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """
    Enhanced user registration form.
    
    Features:
    - Email as primary identifier with domain validation
    - Strong password validation
    - Real-time validation feedback
    - Professional styling
    
    CUSTOMIZATION: Update EMAIL_DOMAIN for your college
    """
    
    # CUSTOMIZE: Change this to your college's email domain
    EMAIL_DOMAIN = '@iiitkottayam.ac.in'
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': f'yourname{EMAIL_DOMAIN}',
            'autocomplete': 'email',
        }),
        help_text=f"Use your official college email address ending with {EMAIL_DOMAIN}"
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'autocomplete': 'given-name',
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'autocomplete': 'family-name',
        })
    )
    
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username (e.g., john_doe)',
            'autocomplete': 'username',
        }),
        help_text="Letters, digits and @/./+/-/_ only. 150 characters or fewer."
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password',
        }),
        help_text=format_html(
            "<small class='form-text text-muted'>"
            "• At least 8 characters<br>"
            "• Not too common<br>"
            "• Not entirely numeric"
            "</small>"
        )
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password',
        }),
        help_text="Enter the same password as before, for verification."
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        """
        Validate email uniqueness and college domain.
        
        CUSTOMIZATION: Update EMAIL_DOMAIN for your college
        """
        email = self.cleaned_data.get('email').lower()
        
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        
        # CUSTOMIZE: Change email domain validation here
        if not email.endswith(self.EMAIL_DOMAIN):
            raise ValidationError(f"Please use your official college email address ending with {self.EMAIL_DOMAIN}")
        
        return email
    
    def clean_username(self):
        """Validate username format and uniqueness."""
        username = self.cleaned_data.get('username')
        
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        
        # Check for valid characters
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters.")
        
        return username
    
    def save(self, commit=True):
        """Save user with email as primary identifier."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    """
    Student profile form for registration and updates.
    
    Features:
    - Comprehensive validation
    - Dynamic field updates
    - User-friendly error messages
    - Bootstrap styling
    
    CUSTOMIZATION: Update roll number validation and department choices
    """
    
    class Meta:
        model = StudentProfile
        fields = [
            'roll_number', 'department', 'year', 
            'phone_number', 'hostel_room', 'emergency_contact'
        ]
        
        widgets = {
            'roll_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2024BCS0001',
                'style': 'text-transform: uppercase;',
            }),
            'department': forms.Select(attrs={
                'class': 'form-control',
            }),
            'year': forms.Select(attrs={
                'class': 'form-control',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 9876543210',
                'type': 'tel',
            }),
            'hostel_room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A-101 or Day Scholar',
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent/Guardian contact',
                'type': 'tel',
            }),
        }
        
        help_texts = {
            'roll_number': 'Format: 2024BCS0001, 2024BCY0002, 2024BCD0003, 2024BEC0004',
            'phone_number': 'Your mobile number for contact',
            'hostel_room': 'Room number if staying in hostel, or "Day Scholar"',
            'emergency_contact': 'Emergency contact number (parent/guardian)',
        }
    
    def clean_roll_number(self):
        """
        Validate roll number format and uniqueness.
        
        CUSTOMIZATION: Update pattern and validation logic for your college
        """
        roll_number = self.cleaned_data.get('roll_number', '').upper()
        
        if not roll_number:
            raise ValidationError("Roll number is required.")
        
        # CUSTOMIZE: Update this pattern for your college's roll number format
        # Current pattern: 2024BCS0001, 2024BCY0002, etc.
        pattern = StudentProfile.ROLL_NUMBER_PATTERN
        if not re.match(pattern, roll_number):
            raise ValidationError(
                f"Invalid roll number format. {StudentProfile.ROLL_NUMBER_HELP}"
            )
        
        # Check uniqueness (exclude current instance for updates)
        queryset = StudentProfile.objects.filter(roll_number=roll_number)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError("This roll number is already registered.")
        
        return roll_number
    
    def clean_phone_number(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone_number', '').strip()
        
        if phone:
            # Remove all non-digit characters except +
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            # Validate format
            if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned_phone):
                raise ValidationError(
                    "Enter a valid phone number (e.g., +91 9876543210)"
                )
            
            return cleaned_phone
        
        return phone


class ProfileUpdateForm(forms.ModelForm):
    """
    Combined form for updating user and student profile information.
    
    Features:
    - Update user and profile data together
    - Selective field updates
    - Validation with current user context
    
    CUSTOMIZATION: Update email domain validation if needed
    """
    
    # User fields
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@iiitkottayam.ac.in',
        })
    )
    
    class Meta:
        model = StudentProfile
        fields = [
            'phone_number', 'hostel_room', 'emergency_contact'
        ]
        
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 9876543210',
                'type': 'tel',
            }),
            'hostel_room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A-101 or Day Scholar',
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent/Guardian contact',
                'type': 'tel',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Pre-populate user fields
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def clean_email(self):
        """Validate email uniqueness (excluding current user)."""
        email = self.cleaned_data.get('email').lower()
        
        if self.user and User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("An account with this email already exists.")
        
        return email
    
    def save(self, commit=True):
        """Save both user and profile data."""
        profile = super().save(commit=False)
        
        if self.user:
            # Update user fields
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            
            if commit:
                self.user.save()
                profile.save()
        
        return profile