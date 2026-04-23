from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..models import Cart, Order, OrderItem
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

def dispatch_item_view(request, item_id):
    if request.user.role != 'vendor':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/dashboard/vendor/?section=pending-order-items')
    
    order_item = get_object_or_404(OrderItem, id=item_id, vendor=request.user.vendor_profile)
    order_item.dispatched = True
    order_item.save()
    
    subject = "Your Order Item Has Been Dispatched - ApexStriker"
    message = f"Hi {order_item.order.customer.user.username},\n\nThe item '{order_item.product.name}' from your order #{order_item.order.id} has been dispatched by the vendor.\n\nThank you for shopping with us!"
    email_thread = threading.Thread(target=send_email_async, args=(subject, message, order_item.order.customer.user.email))
    email_thread.start()
    
    messages.success(request, f"Order item '{order_item.product.name}' marked as dispatched and customer notified.")
    return redirect('/dashboard/vendor/?section=pending-order-items')

def receive_item_view(request, item_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/dashboard/admin/?section=order-items-tracking')
    
    order_item = get_object_or_404(OrderItem, id=item_id)
    order_item.received = True
    order_item.save()
    
    messages.success(request, f"Order item '{order_item.product.name}' marked as received by admin.")
    return redirect('/dashboard/admin/?section=order-items-tracking')

def mark_order_as_pickup(request, order_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/dashboard/admin/?section=shipping-control')
    
    order = get_object_or_404(Order, id=order_id)
    
    for item in order.items.all():
        if not item.dispatched:
            messages.error(request, f"Cannot mark order #{order.id} as in transit. Item '{item.product.name}' is not dispatched yet.")
            return redirect('/dashboard/admin/?section=shipping-control')
        
        if not item.received:
            messages.error(request, f"Cannot mark order #{order.id} as in transit. Item '{item.product.name}' is not received by admin yet.")
            return redirect('/dashboard/admin/?section=shipping-control')
        
    order.status = Order.Status.SHIPPING
    order.save()
    
    subject = "Your Order is Now In Transit - ApexStriker"
    message = f"Hi {order.customer.user.username},\n\nYour order #{order.id} is now in transit. It has been picked up and is on its way to you.\n\nThank you for shopping with us!"
    email_thread = threading.Thread(target=send_email_async, args=(subject, message, order.customer.user.email))
    email_thread.start()
    
    messages.success(request, f"Order #{order.id} marked as picked up and in transit.")
    return redirect('/dashboard/admin/?section=shipping-control')