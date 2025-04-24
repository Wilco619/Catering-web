# catering/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db import transaction

from .models import (
    MenuItem, Category, GalleryImage, EventType, 
    CateringOrder, OrderItem, Testimonial, ContactMessage
)
from .forms import (
    ContactForm, OrderForm, TestimonialForm, 
    MenuItemSelectionForm, OrderItemFormSet
)


# Home View
def home(request):
    featured_items = MenuItem.objects.filter(is_featured=True)[:6]
    categories = Category.objects.all()[:4]
    gallery_images = GalleryImage.objects.filter(featured=True)[:8]
    testimonials = Testimonial.objects.filter(is_approved=True)[:6]
    
    context = {
        'featured_items': featured_items,
        'categories': categories,
        'gallery_images': gallery_images,
        'testimonials': testimonials,
    }
    return render(request, 'catering/home.html', context)


# About View
def about(request):
    return render(request, 'catering/about.html')


# Menu Views
class MenuListView(ListView):
    model = MenuItem
    template_name = 'catering/menu.html'
    context_object_name = 'menu_items'
    paginate_by = 12
    ordering = ['name']  # Add default ordering
    
    def get_queryset(self):
        queryset = MenuItem.objects.select_related('category').all().order_by('name')
        category = self.request.GET.get('category')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__slug=category)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        context['debug'] = settings.DEBUG
        return context


class MenuItemDetailView(DetailView):
    model = MenuItem
    template_name = 'catering/menu_item_detail.html'
    context_object_name = 'menu_item'
    slug_url_kwarg = 'slug'


# Gallery Views
class GalleryView(ListView):
    model = GalleryImage
    template_name = 'catering/gallery.html'
    context_object_name = 'images'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        event_type = self.request.GET.get('event_type')
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_types'] = set(GalleryImage.objects.values_list('event_type', flat=True))
        context['selected_event_type'] = self.request.GET.get('event_type', '')
        return context


# Contact Views
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            
            # Send email notification to admin
            subject = f"New Contact Message: {contact_message.subject}"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = settings.CONTACT_EMAIL  # Define this in settings.py
            
            html_message = render_to_string('catering/emails/contact_notification.html', {
                'contact': contact_message,
            })
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject, plain_message, from_email, [to_email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            # Send confirmation email to user
            user_subject = "We've received your message"
            user_html_message = render_to_string('catering/emails/contact_confirmation.html', {
                'contact': contact_message,
            })
            user_plain_message = strip_tags(user_html_message)
            
            user_email = EmailMultiAlternatives(
                user_subject, user_plain_message, from_email, [contact_message.email]
            )
            user_email.attach_alternative(user_html_message, "text/html")
            user_email.send()
            
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'catering/contact.html', {'form': form})


# Ordering System Views
@login_required
def create_order(request):
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        
        if order_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # First save the order without committing
                    order = order_form.save(commit=False)
                    order.user = request.user
                    order.save()  # Save to get the primary key
                    
                    # Now save the order items
                    order_items = formset.save(commit=False)
                    for item in order_items:
                        item.order = order
                        item.save()
                    
                    messages.success(request, 'Your order has been placed successfully!')
                    return redirect('order_detail', pk=order.id)
            except Exception as e:
                messages.error(request, f'Error creating order: {str(e)}')
                return redirect('create_order')
    else:
        order_form = OrderForm()
        formset = OrderItemFormSet()
    
    context = {
        'order_form': order_form,
        'formset': formset,
        'menu_items': MenuItem.objects.filter(is_available=True),
        'categories': Category.objects.all(),
    }
    return render(request, 'catering/create_order.html', context)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(CateringOrder, pk=pk, user=request.user)
    order_items = order.order_items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'catering/order_detail.html', context)


@login_required
def my_orders(request):
    orders = CateringOrder.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'catering/my_orders.html', context)


@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(CateringOrder, pk=pk, user=request.user)
    
    if order.status in ['pending', 'confirmed']:
        order.status = 'cancelled'
        order.save()
        
        # Send cancellation notification
        subject = f"Order #{order.id} Cancellation Confirmation"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = order.contact_email
        
        html_message = render_to_string('catering/emails/order_cancellation.html', {
            'order': order,
        })
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject, plain_message, from_email, [to_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        messages.success(request, 'Your order has been cancelled successfully.')
    else:
        messages.error(request, 'This order cannot be cancelled at this stage.')
    
    return redirect('order_detail', pk=order.id)


# Testimonial Views
class TestimonialCreateView(LoginRequiredMixin, CreateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = 'catering/testimonial_form.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        messages.success(self.request, 'Thank you for your testimonial! It will be reviewed shortly.')
        return super().form_valid(form)


# AJAX Views for menu selection
@login_required
def load_menu_items(request):
    category_id = request.GET.get('category_id')
    menu_items = MenuItem.objects.filter(category_id=category_id, is_available=True)
    return JsonResponse({
        'menu_items': [{
            'id': item.id,
            'name': item.name,
            'image': item.image.url if item.image and item.image.name else None,
            'price': float(item.price),
            'description': item.description
        } for item in menu_items]
    })


# users/views.py
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import CustomUserCreationForm, CustomUserChangeForm

User = get_user_model()


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = 'home'


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your account has been created successfully! You can now log in.')
        return response


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/emails/password_reset_email.html'
    subject_template_name = 'users/emails/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')