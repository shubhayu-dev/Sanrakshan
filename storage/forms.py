"""
Professional Django forms for storage management.

Features:
- Dynamic item formsets with validation
- Rich form widgets with Bootstrap styling
- Real-time validation and feedback
- Category-based organization
- Advanced form handling
"""

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from decimal import Decimal

from .models import StorageEntry, StoredItem


class StorageEntryForm(forms.ModelForm):
    """
    Form for creating storage entries.
    
    Features:
    - Rich text description with character counter
    - Storage location selection
    - Enhanced validation
    - Professional styling
    """
    
    class Meta:
        model = StorageEntry
        fields = ['description', 'storage_location']
        
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your storage session (optional)...\nExample: "Items for winter break - return after January 15th"',
                'maxlength': 500,
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                'title': 'Optional description to help you remember what you stored'
            }),
            
            'storage_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Main Storage Room, Locker A-1 (if assigned)',
                'maxlength': 100,
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',  
                'title': 'Physical storage location (will be assigned by staff if empty)'
            }),
        }
        
        help_texts = {
            'description': 'Optional notes about your storage session',
            'storage_location': 'Leave empty if you want staff to assign location',
        }
    
    def clean_description(self):
        """Validate and clean description field."""
        description = self.cleaned_data.get('description', '').strip()
        
        if len(description) > 500:
            raise ValidationError("Description cannot exceed 500 characters.")
        
        return description


class StoredItemForm(forms.ModelForm):
    """
    Form for individual stored items.
    
    Features:
    - Category-based organization
    - Quantity validation
    - Value estimation
    - Autocomplete suggestions
    """
    
    class Meta:
        model = StoredItem
        fields = ['item_name', 'category', 'quantity', 'description', 'estimated_value']
        
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'e.g., Laptop, Textbooks, Winter Clothes',
                'maxlength': 200,
                'required': True,
                'data-bs-toggle': 'tooltip',
                'title': 'Name or type of item'
            }),
            
            'category': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'required': True,
            }),
            
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': 1,
                'max': 999,
                'value': 1,
                'required': True,
                'style': 'max-width: 80px;'
            }),
            
            'description': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Brand, color, size, etc. (optional)',
                'maxlength': 300,
            }),
            
            'estimated_value': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': 0,
                'step': '0.01',
                'placeholder': '0.00',
                'style': 'max-width: 100px;',
                'data-bs-toggle': 'tooltip',
                'title': 'Estimated value in INR (optional, for insurance)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add required asterisk to required fields
        self.fields['item_name'].label = format_html('Item Name <span class="text-danger">*</span>')
        self.fields['category'].label = format_html('Category <span class="text-danger">*</span>')
        self.fields['quantity'].label = format_html('Qty <span class="text-danger">*</span>')
        
        # Set initial values
        self.fields['quantity'].initial = 1
    
    def clean_item_name(self):
        """Validate item name."""
        item_name = self.cleaned_data.get('item_name', '').strip()
        
        if not item_name:
            raise ValidationError("Item name is required.")
        
        if len(item_name) < 2:
            raise ValidationError("Item name must be at least 2 characters long.")
        
        return item_name
    
    def clean_quantity(self):
        """Validate quantity."""
        quantity = self.cleaned_data.get('quantity')
        
        if quantity is None or quantity < 1:
            raise ValidationError("Quantity must be at least 1.")
        
        if quantity > 999:
            raise ValidationError("Quantity cannot exceed 999.")
        
        return quantity
    
    def clean_estimated_value(self):
        """Validate estimated value."""
        value = self.cleaned_data.get('estimated_value')
        
        if value is not None:
            if value < 0:
                raise ValidationError("Value cannot be negative.")
            
            if value > Decimal('999999.99'):
                raise ValidationError("Value cannot exceed ₹9,99,999.99")
        
        return value


# Dynamic Item Formset
StoredItemFormSet = inlineformset_factory(
    StorageEntry,
    StoredItem, 
    form=StoredItemForm,
    extra=3,  # Start with 3 empty forms
    min_num=1,  # Require at least 1 item
    max_num=20,  # Maximum 20 items per storage session
    can_delete=True,
    validate_min=True,
    validate_max=True,
)


class ClaimConfirmationForm(forms.Form):
    """
    Form for confirming storage entry claims.
    
    Features:
    - Confirmation checkbox
    - Optional notes
    - Terms acknowledgment
    """
    
    confirm_claim = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label="I confirm that I want to claim these items",
        help_text="Please check this box to confirm your claim"
    )
    
    confirmation_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional notes for the storage staff (optional)...',
            'maxlength': 300,
        }),
        label="Notes for Storage Staff",
        help_text="Optional notes about pickup time, special instructions, etc.",
        max_length=300
    )
    
    acknowledge_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label="I understand that this action cannot be undone",
        help_text="Once claimed, the QR code will be deactivated"
    )
    
    def clean(self):
        """Validate the entire form."""
        cleaned_data = super().clean()
        
        if not cleaned_data.get('confirm_claim'):
            raise ValidationError("You must confirm that you want to claim these items.")
        
        if not cleaned_data.get('acknowledge_terms'):
            raise ValidationError("You must acknowledge the terms to proceed.")
        
        return cleaned_data


class StorageSearchForm(forms.Form):
    """
    Form for searching and filtering storage entries.
    
    Features:
    - Status filtering
    - Date range filtering
    - Item name search
    - Category filtering
    """
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('active', 'Active Storage'),
        ('claimed', 'Claimed Items'),  
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    CATEGORY_CHOICES = [('', 'All Categories')] + StoredItem.CATEGORY_CHOICES
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search items, descriptions...',
        }),
        label="Search"
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label="Status"
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label="Category"
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label="From Date"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label="To Date"
    )
    
    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("'From Date' cannot be later than 'To Date'.")
        
        return cleaned_data


class ItemCategoryUpdateForm(forms.Form):
    """
    Utility form for bulk updating item categories.
    Used in admin interface for data management.
    """
    
    old_category = forms.ChoiceField(
        choices=StoredItem.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="From Category"
    )
    
    new_category = forms.ChoiceField(
        choices=StoredItem.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="To Category"
    )
    
    def clean(self):
        """Ensure categories are different."""
        cleaned_data = super().clean()
        old_cat = cleaned_data.get('old_category')
        new_cat = cleaned_data.get('new_category')
        
        if old_cat == new_cat:
            raise ValidationError("Old and new categories cannot be the same.")
        
        return cleaned_data