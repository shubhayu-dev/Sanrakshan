"""
Django signals for accounts app.
Auto-create student profile when user is created via admin.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, StudentProfile


@receiver(post_save, sender=User)
def create_or_update_student_profile(sender, instance, created, **kwargs):
    """
    Create a student profile when a user is created via admin.
    Only for users created outside of the normal registration flow.
    """
    if created:
        # Check if a profile will be/is being created by registration process
        # We can detect this by checking if we're in a transaction (registration uses atomic)
        from django.db import transaction
        
        # Only create profile if:
        # 1. No profile exists yet
        # 2. We're not in an atomic transaction (which registration uses)
        # 3. User is not a superuser (superusers don't need student profiles automatically)
        if (not StudentProfile.objects.filter(user=instance).exists() and 
            not transaction.get_connection().in_atomic_block and
            not instance.is_superuser):
            
            # Create a minimal profile with valid roll number format
            # Use format: TEMP + year + department + padded user ID
            temp_roll = f'2024BCS{instance.id:04d}'
            
            StudentProfile.objects.create(
                user=instance,
                roll_number=temp_roll,
                department='BCS',
                year=1
            )
