from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
import logging
import re
from twilio.rest import Client
from .models import Property, PropertyImage, Inquiry, SavedProperty, PCMC_AREAS

logger = logging.getLogger(__name__)

def home(request):
    """Home page showing all properties"""
    featured = Property.objects.filter(is_available=True, is_featured=True).order_by('-created_at')[:6]
    latest = Property.objects.filter(is_available=True).order_by('-created_at')[:6]
    stats = {
        'total_properties': Property.objects.filter(is_available=True).count(),
        'total_areas': Property.objects.filter(is_available=True).values_list('area', flat=True).distinct().count(),
    }
    return render(request, 'real_estate_startup/home.html', {
        'featured_properties': featured,
        'latest_properties': latest,
        'stats': stats,
        'page_title': 'Home'
    })

def property_list(request):
    """List all properties with optional filters"""
    properties = Property.objects.filter(is_available=True).order_by('-created_at')
    
    # Get filter parameters
    listing_type = request.GET.get('listing_type', 'buy')
    property_type = request.GET.get('property_type')
    area = request.GET.get('area')
    city = request.GET.get('city')
    bedrooms = request.GET.get('bedrooms')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    furnishing = request.GET.get('furnishing')
    search_query = request.GET.get('q', '')
    
    # Filter by listing type
    if listing_type:
        properties = properties.filter(listing_type=listing_type)
    
    # Apply other filters
    if property_type:
        properties = properties.filter(property_type=property_type)
    if area:
        if area == 'pune':
            properties = properties.filter(city__icontains='pune')
        elif area == 'pcmc':
            pcmc_area_keys = [choice[0] for choice in PCMC_AREAS if choice[0] != 'other']
            properties = properties.filter(
                Q(city__icontains='Pimpri') | Q(area__in=pcmc_area_keys)
            )
        else:
            properties = properties.filter(area=area)
    if city:
        properties = properties.filter(city__icontains=city)
    if bedrooms and bedrooms != 'Any':
        properties = properties.filter(bedrooms__gte=int(bedrooms))
    if min_price:
        properties = properties.filter(price__gte=min_price)
    if max_price:
        properties = properties.filter(price__lte=max_price)
    if furnishing:
        properties = properties.filter(furnishing=furnishing)
    if search_query:
        properties = properties.filter(
            title__icontains=search_query
        ) | properties.filter(
            description__icontains=search_query
        ) | properties.filter(
            address__icontains=search_query
        )
    
    # Get filter options
    areas = Property.objects.filter(is_available=True).values_list('area', flat=True).distinct()
    property_types = Property.objects.filter(is_available=True).values_list('property_type', flat=True).distinct()
    
    context = {
        'properties': properties,
        'areas': areas,
        'property_types': property_types,
        'page_title': 'Properties',
        'current_listing_type': listing_type,
        'search_query': search_query,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        property_list = []
        for prop in properties[:20]:
            property_list.append({
                'id': prop.id,
                'title': prop.title,
                'price': str(prop.price),
                'area': prop.area,
                'bedrooms': prop.bedrooms,
                'image': prop.images.first().image.url if prop.images.first() else '',
            })
        return JsonResponse({'properties': property_list})
    
    return render(request, 'real_estate_startup/property_list.html', context)

def property_detail(request, property_id):
    """Show detailed view of a property"""
    property = get_object_or_404(Property, id=property_id)

    if property.amenities:
        property.amenities_list = property.amenities.split(',')
    images = property.images.all()
    is_saved = False
    
    if request.user.is_authenticated:
        is_saved = SavedProperty.objects.filter(user=request.user, property=property).exists()
    
    # Get related properties in the same area
    related_properties = Property.objects.filter(
        area=property.area, 
        is_available=True,
        listing_type=property.listing_type
    ).exclude(id=property.id)[:3]
    
    return render(request, 'real_estate_startup/property_detail.html', {
        'property': property,
        'images': images,
        'related_properties': related_properties,
        'is_saved': is_saved,
        'page_title': property.title
    })

@login_required(login_url='login')
@require_POST
def toggle_save_property(request, property_id):
    """Toggle save/unsave property for logged-in users"""
    property = get_object_or_404(Property, id=property_id)
    
    saved_property, created = SavedProperty.objects.get_or_create(
        user=request.user,
        property=property
    )
    
    if not created:
        saved_property.delete()
        is_saved = False
        message = 'Property removed from saved'
    else:
        is_saved = True
        message = 'Property saved successfully'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_saved': is_saved, 'message': message})
    
    messages.success(request, message)
    return redirect('property_detail', property_id=property_id)

@login_required(login_url='login')
def saved_properties(request):
    """Show user's saved properties"""
    saved = SavedProperty.objects.filter(user=request.user).select_related('property').order_by('-saved_at')
    properties = [sp.property for sp in saved]
    
    return render(request, 'real_estate_startup/saved_properties.html', {
        'properties': properties,
        'page_title': 'My Saved Properties'
    })


def _normalize_whatsapp_number(number):
    if not number:
        return ''
    normalized = number.strip()
    if normalized.startswith('whatsapp:'):
        normalized = normalized[len('whatsapp:'):]
    normalized = normalized.replace(' ', '').replace('-', '')
    if not re.fullmatch(r'\+\d{10,15}', normalized):
        return ''
    return f'whatsapp:{normalized}'


def _send_whatsapp_inquiry_notification(name, email, phone, property_title):
    logger.info(f"_send_whatsapp_inquiry_notification called with name={name}, email={email}, phone={phone}, property_title={property_title}")
    
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = _normalize_whatsapp_number(getattr(settings, 'TWILIO_WHATSAPP_FROM', ''))
    to_number = _normalize_whatsapp_number(getattr(settings, 'TWILIO_WHATSAPP_TO', ''))

    logger.info(f"Twilio config - SID: {sid[:10] if sid else 'EMPTY'}..., Token: {token[:10] if token else 'EMPTY'}..., From: {from_number}, To: {to_number}")

    if not all([sid, token, from_number, to_number]):
        logger.warning('Twilio WhatsApp not configured correctly: missing or invalid SID/Auth/From/To values.')
        return None

    body = (
        f"New property inquiry for {property_title}\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Phone: {phone}"
    )

    try:
        logger.info(f"Creating Twilio client and sending message to {to_number}")
        client = Client(sid, token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number,
        )
        logger.info(f"WhatsApp message sent successfully. SID: {message.sid}")
        logger.info(f"Message status: {message.status}, Account: {message.account_sid}")
        return True
    except Exception as exc:
        logger.exception('Failed to send WhatsApp inquiry notification: %s', exc)
        return False


def submit_inquiry(request, property_id):
    """Handle inquiry form submission"""
    logger.info(f"submit_inquiry called for property_id={property_id}, method={request.method}")
    
    if request.method == 'POST':
        property = get_object_or_404(Property, id=property_id)
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message')
        
        logger.info(f"Form data received: name={name}, email={email}, phone={phone}")
        
        # Create inquiry
        inquiry = Inquiry.objects.create(
            property=property,
            user=request.user if request.user.is_authenticated else None,
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        
        logger.info(f"Inquiry saved. Now calling _send_whatsapp_inquiry_notification")
        
        sent_whatsapp = _send_whatsapp_inquiry_notification(
            name=name,
            email=email,
            phone=phone,
            property_title=property.title,
        )
        
        logger.info(f"_send_whatsapp_inquiry_notification returned: {sent_whatsapp}")
        
        messages.success(request, 'Your inquiry has been submitted successfully! We will contact you soon.')
        if sent_whatsapp is False:
            messages.warning(request, 'Inquiry saved, but WhatsApp notification failed to send. Check your Twilio credentials and WhatsApp setup.')
        elif sent_whatsapp is None:
            messages.warning(request, 'Inquiry saved, but WhatsApp notification was not sent because Twilio is not configured.')
        return redirect('property_detail', property_id=property_id)
    
    return redirect('property_list')

