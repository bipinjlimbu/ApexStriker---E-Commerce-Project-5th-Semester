from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..models import Cart
import threading

def cart_count(request):
    if request.user.is_authenticated and request.user.role == 'customer':
        cart_items_count = Cart.objects.filter(customer=request.user.customer_profile).count()
        return cart_items_count
    return 0

def send_email_async(subject, message, recipient):
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")
            
@login_required
def cart_view(request):
    cart = Cart.objects.filter(customer=request.user.customer_profile)
    return render(request, 'main/cart_page.html', {'cart_count': cart_count(request), 'cart': cart})