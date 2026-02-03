from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import StorageEntry, StoredItem
from unique_codes.models import QRCodeImage  

@receiver(pre_save, sender=StorageEntry)
def update_storage_status(sender, instance, **kwargs):
    """
    Update storage entry status timestamps when status changes
    """
    if instance.pk:  # If this is an update
        old_instance = StorageEntry.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            # Update timestamp when status changes
            instance.updated_at = timezone.now()
            
            if instance.status == 'claimed':
                instance.claimed_at = timezone.now()
            elif instance.status == 'active':  # Changed from 'stored' to 'active'
                instance.created_at = timezone.now()

@receiver(post_save, sender=StorageEntry)
def create_qr_code(sender, instance, created, **kwargs):
    """
    Generate QR code when storage entry is created
    """
    if created:
        from qr_codes.models import QRCodeImage

        # Avoid double creation if somehow QR already exists
        if not hasattr(instance, 'qr_code'):
            QRCodeImage.objects.create(
                storage_entry=instance,        # link to StorageEntry
                content_data={                 # store info here
                    "entry_id": instance.pk,
                    "student_name": instance.student.user.get_full_name(),
                    "roll_number": instance.student.roll_number,
                    "status": instance.status,
                }
            )


@receiver(post_save, sender=StoredItem)
def update_entry_item_count(sender, instance, **kwargs):
    """
    Update total items count in storage entry when items are added/modified
    """
    entry = instance.storage_entry  # Changed from session to entry
    entry.generate_qr_data()  # Update QR data with new item count
    entry.save()

@receiver(pre_delete, sender=StorageEntry)
def prevent_active_entry_deletion(sender, instance, **kwargs):
    """
    Prevent deletion of active storage entries
    """
    if instance.status == 'active':  # Changed condition to match model's status choices
        raise ValidationError(
            "Cannot delete an active storage entry. "
            "Please claim or cancel the entry first."
        )

def connect_signals():
    """Explicitly connect all signals"""
    pre_save.connect(update_storage_status, sender=StorageEntry)
    post_save.connect(create_qr_code, sender=StorageEntry)
    post_save.connect(update_entry_item_count, sender=StoredItem)
    pre_delete.connect(prevent_active_entry_deletion, sender=StorageEntry)