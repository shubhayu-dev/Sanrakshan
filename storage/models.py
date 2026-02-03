"""
Storage system models for managing student belongings.

Architecture decisions:
- Separate StorageEntry (session) from StoredItem (individual items)
- UUID for QR codes (secure, non-guessable)
- Status tracking with proper state transitions
- Comprehensive audit trail
- Optimized database queries with select_related/prefetch_related
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
import uuid
import json


class StorageEntryManager(models.Manager):
    """Custom manager for StorageEntry with optimized queries."""
    
    def active(self):
        """Get all active storage entries."""
        return self.filter(status='active')
    
    def claimed(self):
        """Get all claimed storage entries."""
        return self.filter(status='claimed')
    
    def for_student(self, student):
        """Get all storage entries for a specific student with related data."""
        return self.select_related('student__user').prefetch_related('items').filter(student=student)


class StorageEntry(models.Model):
    """
    Main storage session for a student's belongings.
    
    Design principles:
    - One entry per storage session (not per item)
    - UUID for secure QR code identification
    - Status tracking for proper workflow
    - Audit trail for accountability
    """
    
    STATUS_CHOICES = [
        ('active', 'Active - Items in Storage'),
        ('claimed', 'Claimed - Items Retrieved'),
        ('expired', 'Expired - Session Ended'),
        ('cancelled', 'Cancelled - Session Cancelled'),
    ]
    
    # Core fields
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='storage_entries',
        db_index=True,
        null=False, blank=False,
        help_text="Student who owns these items"
    )
    
    # UUID for QR code - secure and unguessable
    entry_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique identifier for QR code"
    )
    
    # Storage session details
    description = models.TextField(
        blank=True,
        help_text="Additional notes about this storage session"
    )
    
    # Status management
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    
    # Timestamps for audit trail
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When items were stored"
    )
    
    claimed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When items were claimed"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification time"
    )
    
    # QR code data (JSON string for flexibility)
    qr_code_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured data for QR code display"
    )
    
    # Metadata
    storage_location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Physical storage location (e.g., Shelf A-1)"
    )
    
    staff_notes = models.TextField(
        blank=True,
        help_text="Internal notes for storage staff"
    )
    
    # Custom manager
    objects = StorageEntryManager()
    
    class Meta:
        verbose_name = "Storage Entry"
        verbose_name_plural = "Storage Entries"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['entry_id']),
        ]
        constraints = [
            # Ensure claimed_at is set when status is claimed
            models.CheckConstraint(
                check=models.Q(
                    status__in=['active', 'expired', 'cancelled']
                ) | models.Q(
                    status='claimed',
                    claimed_at__isnull=False
                ),
                name='claimed_at_required_when_claimed'
            )
        ]
    
    def clean(self):
        """Custom validation."""
        super().clean()
        
        # Validate status transitions
        if self.pk:  # Only for existing objects
            old_instance = StorageEntry.objects.get(pk=self.pk)
            if old_instance.status == 'claimed' and self.status != 'claimed':
                raise ValidationError("Cannot change status of already claimed items")
    
    def save(self, *args, **kwargs):
        self.full_clean()

        # Auto-set claimed_at when status changes to claimed
        if self.status == 'claimed' and not self.claimed_at:
            self.claimed_at = timezone.now()

        # Only generate QR if object already has a PK
        if self.pk and not self.qr_code_data:
            self.generate_qr_data()

        super().save(*args, **kwargs)

        # Ensure QR is generated after first save if it was skipped
        if not self.qr_code_data:
            self.generate_qr_data()
            super().save(update_fields=['qr_code_data'])


    
    def __str__(self):
        return f"{self.student.roll_number} - {self.created_at.date()} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        """Get URL for QR code display."""
        return reverse('unique_codes:display', kwargs={'entry_id': self.entry_id})
    
    # Business logic methods
    def claim_items(self, claimed_by=None):
        """
        Mark this storage entry as claimed.
        
        Args:
            claimed_by: User who processed the claim (for audit)
        """
        if self.status != 'active':
            raise ValidationError(f"Cannot claim items with status: {self.status}")
        
        self.status = 'claimed'
        self.claimed_at = timezone.now()
        
        # Add audit information
        if claimed_by:
            if not self.staff_notes:
                self.staff_notes = ""
            self.staff_notes += f"\nClaimed by: {claimed_by} at {timezone.now()}"
        
        self.save()
        
        # Deactivate the QR code
        try:
            qr_code = self.qr_code
            qr_code.is_active = False
            qr_code.save()
        except:
            pass  # QR code might not exist
    
    def cancel_storage(self, reason=""):
        """Cancel this storage entry."""
        if self.status == 'claimed':
            raise ValidationError("Cannot cancel already claimed items")
        
        self.status = 'cancelled'
        if reason:
            self.staff_notes = f"{self.staff_notes}\nCancelled: {reason}" if self.staff_notes else f"Cancelled: {reason}"
        
        self.save()
    
    def generate_qr_data(self):
        """Generate structured data for QR code."""
        self.qr_code_data = {
            'entry_id': str(self.entry_id),
            'student_name': self.student.user.get_full_name(),
            'roll_number': self.student.roll_number,
            'department': self.student.get_department_display(),
            'phone': self.student.phone_number,
            'storage_date': self.created_at.isoformat(),
            'total_items': self.get_total_items(),
            'status': self.status,
        }
    
    # Query methods
    def get_items_list(self):
        """Get all items in this storage entry."""
        return self.items.all().order_by('item_name')
    
    def get_total_items(self):
        """Get total count of individual items (sum of quantities)."""
        return sum(item.quantity for item in self.items.all()) or 0
    
    def get_unique_items(self):
        """Get count of unique item types."""
        return self.items.count()
    
    @property
    def is_active(self):
        """Check if storage entry is active."""
        return self.status == 'active'
    
    @property 
    def is_claimed(self):
        """Check if items have been claimed."""
        return self.status == 'claimed'
    
    @property
    def days_in_storage(self):
        """Calculate how many days items have been in storage."""
        end_date = self.claimed_at if self.claimed_at else timezone.now()
        return (end_date.date() - self.created_at.date()).days


class StoredItem(models.Model):
    """
    Individual items stored within a storage entry.
    
    Features:
    - Support for quantities (multiple same items)
    - Categorization for better organization
    - Rich descriptions for identification
    """
    
    CATEGORY_CHOICES = [
        ('books', 'Books & Study Materials'),
        ('electronics', 'Electronics & Gadgets'),
        ('clothing', 'Clothing & Personal Items'),
        ('stationery', 'Stationery & Supplies'),
        ('sports', 'Sports Equipment'),
        ('misc', 'Miscellaneous'),
    ]
    
    storage_entry = models.ForeignKey(
        StorageEntry,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    item_name = models.CharField(
        max_length=200,
        help_text="Name of the item"
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='misc',
        help_text="Item category for organization"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Number of this item"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Detailed description, color, brand, etc."
    )
    
    estimated_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated value in INR (optional)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Stored Item"
        verbose_name_plural = "Stored Items"
        ordering = ['category', 'item_name']
        indexes = [
            models.Index(fields=['storage_entry', 'category']),
        ]
    
    def clean(self):
        """Custom validation."""
        super().clean()
        
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than 0'})
    
    def save(self, *args, **kwargs):
        """Override save with validation."""
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update parent entry's QR data when items change
        self.storage_entry.generate_qr_data()
        self.storage_entry.save()
    
    def __str__(self):
        if self.quantity > 1:
            return f"{self.item_name} (x{self.quantity})"
        return self.item_name
    
    @property
    def display_name(self):
        """Get formatted display name with quantity."""
        base_name = f"{self.item_name}"
        if self.quantity > 1:
            base_name += f" (x{self.quantity})"
        if self.description:
            base_name += f" - {self.description[:50]}"
        return base_name