# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'company_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'company_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'company_name', 'phone_number', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'company_name'),
        }),
    )


admin.site.register(CustomUser, CustomUserAdmin)


# catering/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, MenuItem, GalleryImage, EventType, 
    CateringOrder, OrderItem, Testimonial, ContactMessage
)


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('name', 'price', 'is_available', 'is_featured')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_menu_items_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    inlines = [MenuItemInline]
    
    def get_menu_items_count(self, obj):
        return obj.menu_items.count()
    get_menu_items_count.short_description = 'Menu Items'


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'is_featured')
    list_filter = ('category', 'is_available', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'is_available', 'is_featured')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'price', 'category')
        }),
        ('Options', {
            'fields': ('is_available', 'is_featured', 'image')
        }),
    )


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'featured', 'created_at', 'image_preview')
    list_filter = ('event_type', 'featured', 'created_at')
    search_fields = ('title', 'description', 'event_type')
    list_editable = ('featured', 'event_type')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('menu_item', 'quantity', 'price', 'subtotal')
    readonly_fields = ('subtotal',)
    
    def subtotal(self, obj):
        return obj.price * obj.quantity
    subtotal.short_description = 'Subtotal'


@admin.register(CateringOrder)
class CateringOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company_name', 'order_type', 'event_date', 'status', 'total_amount')
    list_filter = ('status', 'order_type', 'created_at')
    search_fields = ('user__email', 'company_name', 'delivery_address', 'contact_email')
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'order_type', 'event_type', 'company_name', 'event_date', 'status')
        }),
        ('Contact Details', {
            'fields': ('contact_email', 'contact_phone', 'delivery_address')
        }),
        ('Order Details', {
            'fields': ('number_of_people', 'special_requests', 'total_amount')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        obj.save()
        # Recalculate total amount in case order items were changed
        obj.total_amount = obj.calculate_total()
        obj.save(update_fields=['total_amount'])


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('name', 'company', 'text')
    list_editable = ('is_approved',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        if 'is_read' in form.changed_data and obj.is_read:
            # If marking as read
            obj.is_read = True
        super().save_model(request, obj, form, change)