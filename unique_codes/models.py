import random
import string
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

User = get_user_model()

class UniqueCode(models.Model):
    """
    Model to store and manage Unique Codes for storage entries.
    Replaces the old QR Code image system.
    """
    
    # Use a UUID to avoid predictable URLs
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # Linked to storage entry
    storage_entry = models.OneToOneField(
        'storage.StorageEntry',
        on_delete=models.CASCADE,
        related_name='unique_code'
    )
    
    # THE UNIQUE CODE
    code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        db_index=True,
        help_text="Unique alphanumeric code for manual verification"
    )
    
    # Store the actual image (DEPRECATED - Optional)
    image = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True
    )
    
    # Last regenerated timestamp
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    
    # Metadata
    content_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data metadata"
    )
    
    class Meta:
        verbose_name = "Unique Code"
        verbose_name_plural = "Unique Codes"
        ordering = ['-generated_at']
        db_table = 'qr_codes_qrcodeimage'
    
    def __str__(self):
        return f"Code {self.code} for {self.storage_entry.student.roll_number}"
    
    def get_absolute_url(self):
        return reverse('unique_codes:display', kwargs={'entry_id': self.storage_entry.entry_id})
    
    def generate_unique_code(self):
        """Generate a random unique code."""
        length = 8
        chars = string.ascii_uppercase + string.digits.replace('0', '').replace('O', '') # Avoid confusion
        while True:
            code = ''.join(random.choices(chars, k=length))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            if not UniqueCode.objects.filter(code=formatted_code).exists():
                return formatted_code

    def generate_code_string(self, regenerate=False):
        """
        Generate Unique Code string.
        Renamed from generate_qr_image to be more accurate.
        """
        if self.code and not regenerate:
            return self.code
            
        self.code = self.generate_unique_code()
        self.generated_at = timezone.now()
        self.save()
        
        return self.code


class UniqueCodeScan(models.Model):
    """Tracking of Code validations/scans."""
    
    unique_code = models.ForeignKey(
        UniqueCode,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    
    # Who scanned it
    scanned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='code_scans'
    )
    
    # When and where
    scanned_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Location if available
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Result of scan
    is_valid = models.BooleanField(default=False)
    action_taken = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Code Scan"
        verbose_name_plural = "Code Scans"
        ordering = ['-scanned_at']
        db_table = 'qr_codes_qrscan'
    
    def __str__(self):
        return f"Scan: {self.unique_code.code} at {self.scanned_at}"


@receiver(post_save, sender='storage.StorageEntry')
def create_code_for_storage_entry(sender, instance, created, **kwargs):
    """Create a Unique Code when a storage entry is created."""
    if created:
        code_obj = UniqueCode.objects.create(storage_entry=instance)
        code_obj.generate_code_string()
    else:
        # Update if needed
        try:
            # We reference the related name on StorageEntry, which we need to update in StorageEntry
            # But here we are effectively checking if it exists.
            # The related_name in UniqueCode definitions is 'unique_code'.
            # Previously it was 'qr_code'.
            code_obj = instance.unique_code
            if not code_obj.code:
                code_obj.generate_code_string()
        except UniqueCode.DoesNotExist:
            code_obj = UniqueCode.objects.create(storage_entry=instance)
            code_obj.generate_code_string()
