from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# PCMC Area Choices
PCMC_AREAS = (
    ('hinjewadi', 'Hinjewadi'),
    ('wakad', 'Wakad'),
    ('nigdi', 'Nigdi'),
    ('akurdi', 'Akurdi'),
    ('pimple_saudagar', 'Pimple Saudagar'),
    ('pimple_nilakh', 'Pimple Nilakh'),
    ('bhumkar_chowk', 'Bhumkar Chowk'),
    ('tathawade', 'Tathawade'),
    ('kharadi', 'Kharadi'),
    ('viman_nagar', 'Viman Nagar'),
    ('khadki', 'Khadki'),
    ('chinchwad', 'Chinchwad'),
    ('pimpri', 'Pimpri'),
    ('bhosari', 'Bhosari'),
    ('dapodi', 'Dapodi'),
    ('kasba_pune', 'Kasba (Pune)'),
    ('shivaji_nagar', 'Shivaji Nagar'),
    ('deccan', 'Deccan'),
    ('koregaon_park', 'Koregaon Park'),
    ('other', 'Other'),
)

class Property(models.Model):
    PROPERTY_TYPES = (
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('commercial', 'Commercial'),
        ('flat', 'Flat'),
        ('penthouse', 'Penthouse'),
        ('row_house', 'Row House'),
        ('plot', 'Plot/Land'),
    )
    
    FURNISHING_CHOICES = (
        ('unfurnished', 'Unfurnished'),
        ('semi_furnished', 'Semi-Furnished'),
        ('furnished', 'Furnished'),
    )
    
    LISTING_TYPE_CHOICES = (
        ('buy', 'Buy'),
        ('rent', 'Rent'),
        ('commercial', 'Commercial'),
        ('project', 'Project'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, default='buy')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100, default="Pimpri Chinchwad")
    area = models.CharField(max_length=100, choices=PCMC_AREAS, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    # Basic Details
    bedrooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)
    carpet_area = models.CharField(max_length=50, blank=True, null=True)  # in sq ft
    built_area = models.CharField(max_length=50, blank=True, null=True)  # in sq ft
    # Additional Details
    furnishing = models.CharField(max_length=20, choices=FURNISHING_CHOICES, default='unfurnished')
    property_age = models.CharField(max_length=50, blank=True, null=True)  # e.g., "5 years", "New"
    amenities = models.TextField(blank=True, null=True)  # comma-separated amenities
    facing = models.CharField(max_length=50, blank=True, null=True)  # North, South, etc.
    floor_number = models.CharField(max_length=50, blank=True, null=True)
    total_floors = models.CharField(max_length=50, blank=True, null=True)
    # Seller Info
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties', null=True, blank=True)
    seller_name = models.CharField(max_length=100, blank=True, null=True)
    seller_phone = models.CharField(max_length=15, blank=True, null=True)
    seller_email = models.EmailField(blank=True, null=True)
    # Status
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="property_images/")
    
    def __str__(self):
        return f"Image for {self.property.title}"


class SavedProperty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'property')
    
    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"


class Inquiry(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            regex=r'^\d{10}$',
            message='Phone number must be exactly 10 digits',
            code='invalid_phone'
        )],
        blank=True,
        null=True,
        help_text='10-digit mobile number'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Inquiry for {self.property.title} by {self.name}"

