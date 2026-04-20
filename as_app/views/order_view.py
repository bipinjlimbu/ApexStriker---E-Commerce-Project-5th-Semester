from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..models import Cart
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import threading
import json


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

def update_cart_quantity(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        item_id = data.get('item_id')
        new_qty = data.get('quantity')
        
        # Get item and update
        cart_item = get_object_or_404(Cart, id=item_id, customer=request.user.customer_profile)
        
        # Optional: Stock check logic here
        if cart_item.product.stock < new_qty:
            return JsonResponse({'status': 'error', 'message': 'Insufficient stock'}, status=400)
            
        cart_item.quantity = new_qty
        cart_item.save()
        
        return JsonResponse({'status': 'success', 'message': 'Quantity updated'})
    return JsonResponse({'status': 'error'}, status=400)