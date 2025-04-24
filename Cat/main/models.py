# users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    company_name = models.CharField(_('company name'), max_length=100, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    def __str__(self):
        return self.email


# catering/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class MenuItem(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(
        upload_to='menu_items/', 
        null=True, 
        blank=True,
        default='img/default-menu-item.jpg'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menu_items')
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True)
    
    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return f"{settings.STATIC_URL}img/default-menu-item.jpg"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='gallery/')
    event_type = models.CharField(max_length=50, blank=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


class EventType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='event_types/', blank=True, null=True)
    
    def __str__(self):
        return self.name


class CateringOrder(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    ORDER_TYPE_CHOICES = (
        ('corporate', 'Corporate Catering'),
        ('event', 'Event Catering'),
        ('subscription', 'Subscription Meal'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    event_type = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    company_name = models.CharField(max_length=100, blank=True)
    event_date = models.DateTimeField()
    delivery_address = models.TextField()
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    number_of_people = models.PositiveIntegerField()
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"
    
    def calculate_total(self):
        return sum(item.subtotal for item in self.order_items.all())
    
    def save(self, *args, **kwargs):
        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(CateringOrder, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.company}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return self.subject
