"""
User account models for the student storage system.

Following Django best practices:
- Custom User model for future extensibility
- Proper field validation and constraints
- Clear string representations
- Comprehensive metadata

CUSTOMIZATION GUIDE FOR OTHER COLLEGES:
1. Update DEPARTMENT_CHOICES with your college departments
2. Modify roll number validation in StudentProfile.clean()
3. Change email domain validation in forms.py
4. Update help texts and placeholders as needed
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import random
import string


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Why custom user model?
    - Django strongly recommends this for new projects
    - Allows future customization without complex migrations
    - Better control over user fields and behavior
    
    CUSTOMIZATION: No changes needed for most colleges
    """
    
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
        help_text="Required. Must be a valid college email address."  # Updated help text
    )
    
    # Keep username as primary but ensure email uniqueness
    # USERNAME_FIELD = 'email'  # Commented out to avoid auth issues
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = 'auth_user_custom'  # Avoid conflicts
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username


class StudentProfile(models.Model):
    """
    Extended profile for student-specific information.
    
    Design decisions:
    - OneToOne with User (not extending User directly) for flexibility
    - Comprehensive validation for roll numbers and phone
    - Proper choices for departments and years
    - Indexes for frequently queried fields
    
    CUSTOMIZATION GUIDE:
    1. Update DEPARTMENT_CHOICES with your college's departments
    2. Modify ROLL_NUMBER_PATTERN for your roll number format
    3. Update validation logic in clean() method
    4. Adjust YEAR_CHOICES if needed
    """
    
    # CUSTOMIZE: Update these department choices for your college
    DEPARTMENT_CHOICES = [
        ('BCS', 'Computer Science & Engineering'),
        ('BEC', 'Electronics & Communication Engineering'), 
        ('BCY', 'Cyber Security'),
        ('BCD', 'Computer Science & Design'),
        ('OTHER', 'Other'),
    ]
    
    # CUSTOMIZE: Roll number pattern - currently supports IIIT Kottayam format
    # Format: 2024BCS0001, 2024BCY0002, etc.
    ROLL_NUMBER_PATTERN = r'^(20(?:2[4-9]|[3-9][0-9]))B(CS|CY|CD|EC)([0-9]{4})$'
    ROLL_NUMBER_HELP = "Format: 2024BCS0001, 2024BCY0002, 2024BCD0003, 2024BEC0004"
    
    YEAR_CHOICES = [
        (1, 'First Year'),
        (2, 'Second Year'),
        (3, 'Third Year'),
        (4, 'Fourth Year'),
        (5, 'Fifth Year'),  # For 5-year programs
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    
    roll_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=ROLL_NUMBER_PATTERN,
                message=f'Roll number format: {ROLL_NUMBER_HELP}'
            )
        ],
        help_text=ROLL_NUMBER_HELP,
        db_index=True  # Frequently searched field
    )
    
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text="Contact phone number"
    )
    
    department = models.CharField(
        max_length=10,
        choices=DEPARTMENT_CHOICES,
        help_text="Academic department"
    )
    
    year = models.IntegerField(
        choices=YEAR_CHOICES,
        help_text="Current academic year"
    )
    
    # Additional profile fields
    hostel_room = models.CharField(
        max_length=20,
        blank=True,
        help_text="Hostel room number (if applicable)"
    )
    
    emergency_contact = models.CharField(
        max_length=15,
        blank=True,
        help_text="Emergency contact number"
    )
    
    is_active_student = models.BooleanField(
        default=True,
        help_text="Whether the student is currently enrolled"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"
        ordering = ['roll_number']
        indexes = [
            models.Index(fields=['roll_number']),
            models.Index(fields=['department', 'year']),
        ]
    
    def clean(self):
        """
        Custom validation for the model.
        
        CUSTOMIZATION: Update roll number validation logic here
        """
        super().clean()
        
        # Ensure roll number is uppercase
        if self.roll_number:
            self.roll_number = self.roll_number.upper()
            
            # CUSTOMIZE: Additional roll number validation
            # Extract year and department from roll number for validation
            import re
            match = re.match(self.ROLL_NUMBER_PATTERN, self.roll_number)
            if match and self.department:
                roll_dept = match.group(2)  # Extract department code (CS, CY, CD, EC)
                # Map roll number department to model department
                dept_mapping = {
                    'CS': 'BCS',
                    'CY': 'BCY', 
                    'CD': 'BCD',
                    'EC': 'BEC'
                }
                expected_dept = dept_mapping.get(roll_dept)
                if expected_dept and expected_dept != self.department:
                    raise ValidationError({
                        'roll_number': f'Roll number department ({roll_dept}) must match selected department ({self.department})'
                    })
        
        # Validate year is reasonable
        if self.year and (self.year < 1 or self.year > 5):
            raise ValidationError({'year': 'Year must be between 1 and 5'})
    
    def save(self, *args, **kwargs):
        """Override save to ensure data consistency."""
        self.full_clean()  # Run validation before saving
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"
    
    @property
    def full_info(self):
        """Return comprehensive student information."""
        return f"{self.user.get_full_name()} - {self.roll_number} - {self.get_department_display()} Year {self.year}"


class PasswordResetCode(models.Model):
    """
    Password reset verification codes.
    
    Simple email-based password reset with 6-digit codes.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_code():
        """Generate a 6-digit verification code."""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_valid(self):
        """Check if code is still valid (not used and within 15 minutes)."""
        if self.is_used:
            return False
        
        # Code expires after 15 minutes
        expiry_time = self.created_at + timezone.timedelta(minutes=15)
        return timezone.now() < expiry_time
    
    def mark_used(self):
        """Mark code as used."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Reset code for {self.email} - {self.code}"