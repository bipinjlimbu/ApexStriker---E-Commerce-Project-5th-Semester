from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..models import Product, Cart, Order, OrderItem, Disbursement
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import models
from decimal import Decimal
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
def add_to_cart_view(request, product_id):
    if request.user.role != 'customer':
        messages.error(request, "Only customers can add items to the cart.")
        return redirect('/products/')
    
    customer = request.user.customer_profile
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect('/marketplace/')
    
    if Cart.objects.filter(customer=customer, product=product).exists():
        messages.info(request, "This product is already in your cart.")
        return redirect(f'/products/{product_id}/')
    
    cart_item, created = Cart.objects.get_or_create(customer=customer, product_id=product_id) 
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, "Item added to cart successfully.")
    return redirect(f'/products/{product_id}/')

@login_required
def cart_view(request):
    cart = Cart.objects.filter(customer=request.user.customer_profile)
    return render(request, 'main/cart_page.html', {'cart_count': cart_count(request), 'cart': cart})

@login_required
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

@login_required
def remove_from_cart_view(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, customer=request.user.customer_profile)
    cart_item.delete()
    messages.success(request, "Item removed from cart successfully.")
    return redirect('/cart/')

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

def mark_order_as_shipped(request, order_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/dashboard/admin/?section=shipping-control')
    
    order = get_object_or_404(Order, id=order_id)
    
    if order.status != Order.Status.SHIPPING:
        messages.error(request, f"Cannot mark order #{order.id} as shipped. It is not in transit yet.")
        return redirect('/dashboard/admin/?section=shipping-control')
    
    order.status = Order.Status.SHIPPED
    order.save()
    
    subject = "Your Order Has Been Shipped - ApexStriker"
    confirm_url = "/dashboard/customer/?section=my-orders"
    message = f"Hi {order.customer.user.username},\n\nYour order #{order.id} has been shipped. You can Pick Up the item at the designated location and also Confirm Your Delivery here \n {confirm_url}.\n\nThank you for shopping with us!"
    email_thread = threading.Thread(target=send_email_async, args=(subject, message, order.customer.user.email))
    email_thread.start()
    
    messages.success(request, f"Order #{order.id} marked as shipped and customer notified.")
    return redirect('/dashboard/admin/?section=shipping-control')

def confirm_delivery_view(request, order_id):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/dashboard/customer/?section=my-orders')
    
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer_profile)
    
    if order.status != Order.Status.SHIPPED:
        messages.error(request, f"Cannot confirm delivery for order #{order.id}. It has not been marked as shipped yet.")
        return redirect('/dashboard/customer/?section=my-orders')
    
    order.status = Order.Status.COMPLETED
    order.save()
    
    vendors = OrderItem.objects.filter(order=order).values_list('vendor', flat=True).distinct()
    
    for vendor in vendors:
        vendor_items = OrderItem.objects.filter(order=order, vendor_id=vendor)
        total_amount = sum(item.total_price for item in vendor_items)
        
        admin_commission = total_amount * Decimal('0.10')
        payout_amount = total_amount - admin_commission
        
        disbursement = Disbursement.objects.create(
            order=order,
            vendor_id=vendor,
            admin_commission=admin_commission,
            payout_amount=payout_amount
        )
        disbursement.save()
    
    subject = "Order Delivery Confirmed - ApexStriker"
    message = f"Hi {order.customer.user.username},\n\nThank you for confirming the delivery of your order #{order.id}. We hope you enjoy your purchase!\n\nBest regards,\nApexStriker Team"
    email_thread = threading.Thread(target=send_email_async, args=(subject, message, order.customer.user.email))
    email_thread.start()
    
    messages.success(request, f"Thank you for confirming delivery of order #{order.id}.")
    return redirect('/dashboard/customer/?section=my-orders')

def cancel_order_view(request, order_id):
    if not request.user.is_authenticated or request.user.role != 'customer':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')
    
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer_profile)
    
    if order.status != 'paid':
        messages.error(request, "Only paid orders can be cancelled.")
        return redirect('/dashboard/customer/')
    
    for item in order.items.all():
        product = item.product
        product.stock += item.quantity
        product.save()
        
    order.status = 'cancelled'
    order.save()
    
    subject = "ApexStriker - Order Cancelled"
    message = f"Hi {request.user.first_name},\n\nYour order #{order.id} has been cancelled successfully. If you have any questions, please contact our support team.\n\nThank you for being a part of ApexStriker!"
    threading.Thread(target=send_email_async, args=(subject, message, request.user.email)).start()
    
    messages.success(request, f"Order #{order.id} has been cancelled successfully.")
    return redirect('/dashboard/customer/?section=my-orders')

def remove_order_view(request, order_id):
    if not request.user.is_authenticated or request.user.role != 'customer':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')
    
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer_profile)
    
    if order.status != 'cancelled':
        messages.error(request, "Only cancelled orders can be removed.")
        return redirect('/dashboard/customer/')
    
    id = order.id
    order.delete()
    
    messages.success(request, f"Order #{id} has been removed from your history.")
    return redirect('/dashboard/customer/?section=my-orders')