# project/urls.py (main project URLs)
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    CustomLoginView, CustomLogoutView, SignUpView, 
    ProfileUpdateView, CustomPasswordResetView, CustomPasswordResetConfirmView
)


# catering/urls.py (app-specific URLs)
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
    
    # Password Reset URLs
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Menu URLs
    path('menu/', views.MenuListView.as_view(), name='menu'),
    path('menu/<slug:slug>/', views.MenuItemDetailView.as_view(), name='menu_item_detail'),
    
    # Gallery URLs
    path('gallery/', views.GalleryView.as_view(), name='gallery'),
    
    # Order URLs
    path('order/create/', views.create_order, name='create_order'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/', views.my_orders, name='my_orders'),
    path('order/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    
    # AJAX URLs
    path('ajax/load-menu-items/', views.load_menu_items, name='ajax_load_menu_items'),
    
    # Testimonial URLs
    path('testimonial/add/', views.TestimonialCreateView.as_view(), name='add_testimonial'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
