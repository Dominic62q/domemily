from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from rest_framework import generics
from .models import Product, ContactMessage, AboutContent
from .serializers import ProductSerializer, ContactMessageSerializer
import os

# Try to import cloudinary (may fail if not configured)
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
    if CLOUDINARY_URL:
        cloudinary.config(cloudinary_url=CLOUDINARY_URL)
        CLOUDINARY_ENABLED = True
    else:
        CLOUDINARY_ENABLED = False
except ImportError:
    CLOUDINARY_ENABLED = False


def upload_to_cloudinary(file, folder="domemily/products", resource_type="image"):
    """
    Upload file to Cloudinary and return the URL.
    resource_type can be 'image' or 'video'.
    """
    if not CLOUDINARY_ENABLED:
        return None
    try:
        # We must specify resource_type for videos
        result = cloudinary.uploader.upload(file, folder=folder, resource_type=resource_type)
        return result.get('secure_url')
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None


def home(request):
    """Landing page view."""
    return render(request, "fashion/home.html")


def collection(request):
    """View for the dedicated collection page."""
    products = Product.objects.filter(is_available=True).order_by('-created_at')
    return render(request, "fashion/collection.html", {
        "products": products
    })


def about(request):
    """About page with dynamic content."""
    content = AboutContent.objects.first()
    return render(request, "fashion/about.html", {
        "content": content
    })


def contact(request):
    return render(request, "fashion/contact.html")


def product_detail(request, slug):
    """View for individual product detail page."""
    product = get_object_or_404(Product, slug=slug)
    
    # Get related products (same category, excluding current product)
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(id=product.id).order_by('-created_at')[:4]
    
    return render(request, "fashion/product_detail.html", {
        "product": product,
        "related_products": related_products
    })


# --- DASHBOARD & MANAGEMENT VIEWS ---

def upload_dress(request):
    """View for uploading new dresses."""
    context = {
        'dress_types': Product.DRESS_TYPE_CHOICES,
        'recent_products': Product.objects.filter(category='dresses').order_by('-created_at')[:4],
        'form_data': {},
    }
    
    if request.method == 'POST':
        errors = []
        
        # Get form data
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '').strip()
        description = request.POST.get('description', '').strip()
        dress_type = request.POST.get('dress_type', '').strip()
        is_available = request.POST.get('is_available') == 'on'
        image_file = request.FILES.get('image')
        video_file = request.FILES.get('video')
        
        # Store form data for repopulation
        context['form_data'] = {
            'name': name,
            'price': price,
            'description': description,
            'dress_type': dress_type,
        }
        
        # Validation
        if not name:
            errors.append('Dress name is required.')
        if not price:
            errors.append('Price is required.')
        else:
            try:
                price = float(price)
                if price < 0:
                    errors.append('Price must be a positive number.')
            except ValueError:
                errors.append('Invalid price format.')
        
        # --- FIX: Allow upload if EITHER image OR video is provided ---
        if not image_file and not video_file:
            errors.append('Please upload either an image or a video.')
        
        if errors:
            context['errors'] = errors
        else:
            # 1. Handle Image
            image_url = None
            if image_file:
                image_url = upload_to_cloudinary(image_file, resource_type="image")
            
            # 2. Handle Video
            video_url = None
            if video_file:
                video_url = upload_to_cloudinary(video_file, resource_type="video")
            
            # Create Product
            product = Product(
                name=name,
                category='dresses',
                dress_type=dress_type,
                description=description,
                price=price,
                
                # Image Logic
                image_url=image_url if image_url else "",
                image=None if image_url else image_file,
                
                # Video Logic
                video_url=video_url if video_url else "",
                video=None if video_url else video_file,
                
                is_available=is_available,
            )
            product.save()
            
            messages.success(request, f'"{name}" has been uploaded successfully!')
            return redirect('manage_dresses')
    
    return render(request, "fashion/upload_dress.html", context)


def manage_dresses(request):
    """View for managing all dresses."""
    products = Product.objects.filter(category='dresses').order_by('-created_at')
    
    # Filter by status
    current_filter = request.GET.get('filter', '')
    if current_filter == 'available':
        products = products.filter(is_available=True)
    elif current_filter == 'hidden':
        products = products.filter(is_available=False)
    
    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Counts for filter tabs
    all_dresses = Product.objects.filter(category='dresses')
    
    context = {
        'products': products,
        'current_filter': current_filter,
        'search_query': search_query,
        'all_count': all_dresses.count(),
        'available_count': all_dresses.filter(is_available=True).count(),
        'hidden_count': all_dresses.filter(is_available=False).count(),
    }
    
    return render(request, "fashion/manage_dresses.html", context)


def edit_dress(request, product_id):
    """View for editing a dress."""
    product = get_object_or_404(Product, id=product_id, category='dresses')
    
    context = {
        'product': product,
        'dress_types': Product.DRESS_TYPE_CHOICES,
    }
    
    if request.method == 'POST':
        errors = []
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '').strip()
        description = request.POST.get('description', '').strip()
        dress_type = request.POST.get('dress_type', '').strip()
        is_available = request.POST.get('is_available') == 'on'
        image_file = request.FILES.get('image')
        video_file = request.FILES.get('video')
        
        if not name: errors.append('Dress name is required.')
        if not price: errors.append('Price is required.')
        else:
            try:
                price = float(price)
                if price < 0: errors.append('Price must be a positive number.')
            except ValueError: errors.append('Invalid price format.')
        
        if errors:
            context['errors'] = errors
        else:
            product.name = name
            product.dress_type = dress_type
            product.description = description
            product.price = price
            product.is_available = is_available
            
            # Update Image
            if image_file:
                image_url = upload_to_cloudinary(image_file, resource_type="image")
                if image_url:
                    product.image_url = image_url
                    product.image = None
                else:
                    product.image = image_file
                    product.image_url = ""
            
            # Update Video
            if video_file:
                video_url = upload_to_cloudinary(video_file, resource_type="video")
                if video_url:
                    product.video_url = video_url
                    product.video = None
                else:
                    product.video = video_file
                    product.video_url = ""
            
            product.save()
            context['success'] = True
            context['product'] = product
    
    return render(request, "fashion/edit_dress.html", context)


def edit_about(request):
    """View to manage About Page content (Founder & Studio images)."""
    content = AboutContent.objects.first()
    if not content:
        content = AboutContent()
        content.save()
    
    if request.method == 'POST':
        founder_file = request.FILES.get('founder_image')
        studio_file = request.FILES.get('studio_image')
        
        if founder_file:
            url = upload_to_cloudinary(founder_file, folder="domemily/about", resource_type="image")
            if url:
                content.founder_image_url = url
                content.founder_image = None
            else:
                content.founder_image = founder_file
                content.founder_image_url = ""
        
        if studio_file:
            url = upload_to_cloudinary(studio_file, folder="domemily/about", resource_type="image")
            if url:
                content.studio_image_url = url
                content.studio_image = None
            else:
                content.studio_image = studio_file
                content.studio_image_url = ""
                
        content.save()
        messages.success(request, 'About page content updated successfully!')
        return redirect('edit_about')

    return render(request, "fashion/edit_about.html", {'content': content})


def toggle_dress(request, product_id):
    """Toggle dress availability."""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.is_available = not product.is_available
        product.save()
        
        status = "visible" if product.is_available else "hidden"
        messages.success(request, f'"{product.name}" is now {status}.')
    
    return redirect('manage_dresses')


def delete_dress(request, product_id):
    """Delete a dress."""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" has been deleted.')
    
    return redirect('manage_dresses')


# --- API VIEWS ---

class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer

class ContactCreateAPIView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer