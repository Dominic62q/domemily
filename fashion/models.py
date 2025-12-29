from django.db import models
from django.utils.text import slugify

class Product(models.Model):
    # Main category choices
    CATEGORY_CHOICES = [
        ('dresses', 'Dresses'),
        ('tops', 'Tops'),
        ('bottoms', 'Bottoms'),
        ('outerwear', 'Outerwear'),
        ('accessories', 'Accessories'),
    ]
    
    # Dress type choices (subcategory for dresses)
    DRESS_TYPE_CHOICES = [
        ('', 'Not Applicable'),
        ('kente', 'Kente Dress'),
        ('ankara', 'Ankara Dress'),
        ('kaba_slit', 'Kaba & Slit'),
        ('african_print', 'African Print Dress'),
        ('dashiki', 'Dashiki Dress'),
        ('maxi', 'Maxi Dress'),
        ('midi', 'Midi Dress'),
        ('mini', 'Mini Dress'),
        ('bodycon', 'Bodycon Dress'),
        ('a_line', 'A-Line Dress'),
        ('wrap', 'Wrap Dress'),
        ('shift', 'Shift Dress'),
        ('peplum', 'Peplum Dress'),
        ('mermaid', 'Mermaid Dress'),
        ('ball_gown', 'Ball Gown'),
        ('evening_gown', 'Evening Gown'),
        ('cocktail', 'Cocktail Dress'),
        ('wedding', 'Wedding Dress'),
        ('bridesmaid', 'Bridesmaid Dress'),
        ('casual', 'Casual Dress'),
        ('office', 'Office Dress'),
        ('custom', 'Custom Design'),
    ]

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='dresses')
    
    # Optional Dress Type
    dress_type = models.CharField(max_length=50, choices=DRESS_TYPE_CHOICES, blank=True, default='')
    
    # Optional Description
    description = models.TextField(blank=True)
    
    price = models.DecimalField(max_digits=8, decimal_places=2)
    
    # --- IMAGE FIELDS ---
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)

    # --- VIDEO FIELDS (NEW) ---
    video = models.FileField(upload_to="products/videos/", blank=True, null=True)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_image_display_url(self):
        """Return Cloudinary URL if available, otherwise local image URL."""
        if self.image_url:
            return self.image_url
        elif self.image:
            return self.image.url
        return ''

    def get_video_display_url(self):
        """Return Cloudinary URL if available, otherwise local video URL."""
        if self.video_url:
            return self.video_url
        elif self.video:
            return self.video.url
        return None

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_dress_type_display_safe(self):
        """Return dress type display or empty string if not applicable."""
        if self.dress_type:
            return self.get_dress_type_display()
        return ""


class AboutContent(models.Model):
    """Model to manage images for the About page (Singleton)."""
    founder_image = models.ImageField(upload_to="about/", blank=True, null=True)
    founder_image_url = models.URLField(max_length=500, blank=True, null=True)
    
    studio_image = models.ImageField(upload_to="about/", blank=True, null=True)
    studio_image_url = models.URLField(max_length=500, blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and AboutContent.objects.exists():
            existing = AboutContent.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    def __str__(self):
        return "About Page Content"
    
    def get_founder_display_url(self):
        if self.founder_image_url: return self.founder_image_url
        if self.founder_image: return self.founder_image.url
        return None

    def get_studio_display_url(self):
        if self.studio_image_url: return self.studio_image_url
        if self.studio_image: return self.studio_image.url
        return None


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name