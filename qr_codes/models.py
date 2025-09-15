"""QR code generation and management models.

Features:
- Auto-generated QR code images for storage entries
- Tracking of QR code scans for security
- Secure validation of QR code authenticity
- Support for dynamic data embedding
"""

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import qrcode
import uuid
import os

User = get_user_model()

class QRCodeImage(models.Model):
    """Model to store and manage QR code images for storage entries."""
    
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
    
    # Store the actual image
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
        help_text="Data embedded in the QR code"
    )
    
    class Meta:
        verbose_name = "QR Code Image"
        verbose_name_plural = "QR Code Images"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"QR Code for {self.storage_entry.student.roll_number} - {self.uuid}"
    
    def get_absolute_url(self):
        return reverse('qr_codes:display', kwargs={'entry_id': self.storage_entry.entry_id})
    
    def generate_qr_image(self, regenerate=False):
        """Generate or regenerate the QR code image."""
        if self.image and not regenerate:
            return
            
        # Get data from storage entry
        items_text = []
        for item in self.storage_entry.items.all():
            item_desc = f"• {item.item_name} (x{item.quantity})"
            if item.description:
                item_desc += f" - {item.description}"
            items_text.append(item_desc)

        data = f"""STORAGE ENTRY
        Owner: {self.storage_entry.student.user.get_full_name()}
        Roll: {self.storage_entry.student.roll_number}
        Phone: {self.storage_entry.student.phone_number}

        Storage Date: {self.storage_entry.created_at.strftime('%Y-%m-%d %H:%M')}
        Status: {self.storage_entry.status.title()}

        ITEMS ({len(items_text)}):
        {chr(10).join(items_text)}

        Entry ID: {self.storage_entry.entry_id}"""
        
        # Store the data for future reference
        self.content_data = data
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        # Add student information to top of the image
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to RGB (in case it's not) and add some styling
        img = img.convert('RGB')
        
        # Add student name and info text at the bottom
        student_name = self.storage_entry.student.user.get_full_name()
        roll_number = self.storage_entry.student.roll_number
        
        # Create a larger image with space for text
        width, height = img.size
        new_img = Image.new('RGB', (width, height + 60), color='white')
        new_img.paste(img, (0, 0))
        
        # Add text
        draw = ImageDraw.Draw(new_img)
        # Use default font since custom fonts might not be available
        draw.text((10, height + 10), f"Student: {student_name}", fill='black')
        draw.text((10, height + 30), f"Roll #: {roll_number}", fill='black')
        
        # Save the image to a BytesIO buffer
        buffer = BytesIO()
        new_img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Generate a filename
        filename = f"qr_{self.storage_entry.entry_id}.png"
        
        # Delete old image if it exists
        if self.image:
            self.image.delete(save=False)
            
        # Save new image
        self.image.save(filename, ContentFile(buffer.read()), save=False)
        self.generated_at = timezone.now()
        self.save()
        
        return self.image


class QRScan(models.Model):
    """Tracking of QR code scans for security auditing."""
    
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
        verbose_name = "QR Code Scan"
        verbose_name_plural = "QR Code Scans"
        ordering = ['-scanned_at']
    
    def __str__(self):
        return f"Scan: {self.qr_code} at {self.scanned_at}"


@receiver(post_save, sender='storage.StorageEntry')
def create_qr_code_for_storage_entry(sender, instance, created, **kwargs):
    """Create a QR code image when a storage entry is created."""
    if created:
        QRCodeImage.objects.create(storage_entry=instance)
    else:
        # Update QR code if entry data has changed
        try:
            qr_code = instance.qr_code
            if qr_code:
                qr_code.generate_qr_image(regenerate=True)
        except QRCodeImage.DoesNotExist:
            # Create if it doesn't exist yet
            QRCodeImage.objects.create(storage_entry=instance)
