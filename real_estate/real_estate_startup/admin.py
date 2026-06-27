from django.contrib import admin
from .models import Property, PropertyImage, Inquiry, SavedProperty

# Inline for Property Images - allows adding images directly in Property admin
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1  # Number of empty rows to display for adding new images
    fields = ['image', 'preview']
    readonly_fields = ['preview']
    
    def preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="100" style="border-radius: 5px;" />', obj.image.url)
        return "No image"
    preview.short_description = "Preview"

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'property_type', 'listing_type', 'area', 'price', 'bedrooms', 'is_available', 'is_featured', 'created_at']
    list_filter = ['property_type', 'listing_type', 'area', 'is_available', 'is_featured', 'furnishing']
    search_fields = ['title', 'address', 'city', 'area', 'description']
    inlines = [PropertyImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'property_type', 'listing_type', 'price')
        }),
        ('Location', {
            'fields': ('address', 'city', 'area', 'pincode')
        }),
        ('Property Details', {
            'fields': ('bedrooms', 'bathrooms', 'carpet_area', 'built_area', 'furnishing', 'property_age', 'floor_number', 'total_floors', 'facing')
        }),
        ('Amenities', {
            'fields': ('amenities',),
            'classes': ('collapse',)
        }),
        ('Seller Information', {
            'fields': ('posted_by', 'seller_name', 'seller_phone', 'seller_email'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_available', 'is_featured')
        }),
    )

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'property', 'phone', 'is_read', 'created_at']
    list_filter = ['created_at', 'is_read']
    search_fields = ['name', 'email', 'message', 'phone']
    readonly_fields = ['created_at']


@admin.register(SavedProperty)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display = ['user', 'property', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__username', 'property__title']




