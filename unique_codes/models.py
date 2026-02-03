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

class QRCodeImage(models.Model):
    """
    Model to store and manage Unique Codes for storage entries.
    Renamed conceptually to UniqueCode but keeping model name for DB compatibility if needed, 
    or we can rename it. For now, we'll keep the class name but change functionality 
    to be a 'Unique Code' manager.
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
        related_name='qr_code'
    )
    
    # THE UNIQUE CODE (Replacement for Image)
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
            if not QRCodeImage.objects.filter(code=formatted_code).exists():
                return formatted_code

    def generate_qr_image(self, regenerate=False):
        """
        Refactored to generate Unique Code string instead of Image.
        Kept name 'generate_qr_image' for compatibility with existing calls,
        but it now primarily ensures a 'code' exists.
        """
        if self.code and not regenerate:
            return self.code
            
        self.code = self.generate_unique_code()
        self.generated_at = timezone.now()
        self.save()
        
        return self.code


class QRScan(models.Model):
    """Tracking of Code validations/scans."""
    
    qr_code = models.ForeignKey(
        QRCodeImage,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    
    # Who scanned it
    scanned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_scans'
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
        return f"Scan: {self.qr_code.code} at {self.scanned_at}"


@receiver(post_save, sender='storage.StorageEntry')
def create_qr_code_for_storage_entry(sender, instance, created, **kwargs):
    """Create a Unique Code when a storage entry is created."""
    if created:
        qr = QRCodeImage.objects.create(storage_entry=instance)
        qr.generate_qr_image() # This now generates the alphanumeric code
    else:
        # Update if needed
        try:
            qr_code = instance.qr_code
            if not qr_code.code:
                qr_code.generate_qr_image()
        except QRCodeImage.DoesNotExist:
            qr = QRCodeImage.objects.create(storage_entry=instance)
            qr.generate_qr_image()
