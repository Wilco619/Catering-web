# catering/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    ContactMessage, CateringOrder, OrderItem,
    MenuItem, Testimonial
)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your Message', 'rows': 5}),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = CateringOrder
        fields = [
            'order_type', 'event_type', 'company_name', 'event_date', 
            'delivery_address', 'contact_phone', 'contact_email', 
            'number_of_people', 'special_requests'
        ]
        widgets = {
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'event_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local',
                'min': f"{forms.fields.datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')}"
            }),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'number_of_people': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'price']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-select menu-item-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'price': forms.HiddenInput(),
        }


# Create the formset for OrderItems
OrderItemFormSet = inlineformset_factory(
    CateringOrder, 
    OrderItem,
    form=OrderItemForm,
    extra=1, 
    can_delete=True
)


class MenuItemSelectionForm(forms.Form):
    """Form to select menu items with quantities"""
    category = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select a Category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Category
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'company', 'text', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
        }


# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'company_name', 'phone_number', 'address']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class CustomUserChangeForm(UserChangeForm):
    password = None  # Remove password field from the form
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'company_name', 'phone_number', 'address']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }