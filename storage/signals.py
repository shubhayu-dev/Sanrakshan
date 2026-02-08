from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import StorageEntry, StoredItem
from unique_codes.models import UniqueCode  

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




@receiver(post_save, sender=StoredItem)
def update_entry_item_count(sender, instance, **kwargs):
    """
    Update total items count in storage entry when items are added/modified
    """
    entry = instance.storage_entry  # Changed from session to entry
    # entry.unique_code.generate_code_string() # This method doesn't take params anymore/might not need explicit call if just updating metadata?
    # actually models.py says generate_code_string(regenerate=False)
    # But wait, looking at models.py in unique_codes, create_code_for_storage_entry (which is a signal there) seems to handle creation.
    # In `storage/signals.py` line 34, it was creating `QRCodeImage`.
    # unique_codes/models.py has its own signal `create_code_for_storage_entry` (lines 142-161).
    # This might be redundant or conflicting.
    # However, I should stick to the plan: Fix the import and rename.
    # If `unique_codes` app already has a signal for this, maybe I should REMOVE this signal from `storage/signals.py` to avoid duplicates?
    # The user said "fix it", and "remove discrepency".
    # unique_codes/models.py lines 142-161 ALREADY handles creation of UniqueCode on StorageEntry post_save.
    # So `storage/signals.py` lines 24-43 `create_qr_code` is definitely REDUNDANT and CAUSING ERROR (wrong import).
    # I should remove `create_qr_code` from `storage/signals.py`.
    # And `update_entry_item_count` at line 46 calls `entry.generate_qr_data()`.
    # I need to check if `generate_qr_data` exists on StorageEntry model.
    pass

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