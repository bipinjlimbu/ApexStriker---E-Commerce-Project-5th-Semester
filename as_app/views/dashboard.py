from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.contrib import messages
from ..models import User, Vendor, Brand, Product, Order, Wishlist, OrderItem, Disbursement
import threading
    
def send_email_async(subject, message, recipient):
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")
            
@login_required
def admin_dashboard_view(request):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to access the admin dashboard.")
        return redirect('/')
    
    section = request.GET.get('section', 'member-list')
    
    context = {
        'section' : section,
        'total_pending_vendors': Vendor.objects.filter(status=Vendor.Status.PENDING).count(),
        'total_pending_payouts': Disbursement.objects.filter(is_transferred=False).count(),
        'total_products_reviews': 350,
        'total_admin_revenue': sum(disbursement.admin_commission for disbursement in Disbursement.objects.filter(is_transferred=True)),
        'total_vendor_revenue': sum(disbursement.payout_amount for disbursement in Disbursement.objects.filter(is_transferred=True)),
        'total_revenue': sum(disbursement.total_amount for disbursement in Disbursement.objects.filter(is_transferred=True)),
    }
    
    if section == 'member-list':
        context['members'] = User.objects.all().order_by('-date_joined')
        
    elif section == 'pending-vendors':
        context['vendors'] = Vendor.objects.filter(status=Vendor.Status.PENDING).order_by('-requested_on')
        
    elif section == 'brand-management':
        context['brands'] = Brand.objects.all()
        
    elif section == 'order-items-tracking':
        q = request.GET.get('q', '')
        status = request.GET.get('status', 'all')
        sort = request.GET.get('sort', 'latest')
        
        order_items = OrderItem.objects.filter(order__status='paid').order_by('-order__created_at')
        
        if q:
            query = Q(order__id__icontains=q) | Q(vendor__shop_name__icontains=q) | Q(product__name__icontains=q) | Q(product__brand__name__icontains=q) | Q(product__category__icontains=q)
            order_items = order_items.filter(query).distinct()
            
        if status != 'all' and status == 'pending':
            order_items = order_items.filter(dispatched=False).distinct()
        elif status != 'all' and status == 'dispatched':
            order_items = order_items.filter(dispatched=True, received=False).distinct()
        elif status != 'all' and status == 'received':
            order_items = order_items.filter(dispatched=True, received=True).distinct()
        
        if sort == 'latest':
            order_items = order_items.order_by('-order__created_at')
        elif sort == 'oldest':
            order_items = order_items.order_by('order__created_at')
        elif sort == 'amount_desc':
            order_items = order_items.annotate(price=F('price_at_purchase') * F('quantity')).order_by('-price')
        elif sort == 'amount_asc':
            order_items = order_items.annotate(price=F('price_at_purchase') * F('quantity')).order_by('price')
            
        context['order_items'] = order_items

    elif section == 'shipping-control':
        context['shipping_orders'] = Order.objects.all().order_by('-created_at')
        
    elif section == 'pending-payout':
        context['pending_payouts'] = Disbursement.objects.filter(is_transferred=False).order_by('-created_at')
        
    elif section == 'product-reviews':
        context['product_reviews'] = None
        
    elif section == 'revenue-logs':
        context['revenue_logs'] = Disbursement.objects.filter(is_transferred=True).order_by('-created_at')

    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def approve_vendor_view(request, vendor_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')
    
    try:
        vendor = Vendor.objects.get(id=vendor_id)
        vendor.status = Vendor.Status.APPROVED
        vendor.save()
        
        subject = "ApexStriker - Vendor Application Approved"
        message = f"Hi {vendor.user.first_name},\n\nCongratulations! Your vendor application for '{vendor.shop_name}' has been approved. You can now log in to your vendor dashboard and start listing your products.\n\nThank you for being a part of ApexStriker!"
        threading.Thread(target=send_email_async, args=(subject, message, vendor.user.email)).start()
        
        messages.success(request, f"Vendor '{vendor.shop_name}' has been approved successfully.")
    except Vendor.DoesNotExist:
        messages.error(request, "Vendor not found.")
    
    return redirect('/dashboard/admin/?section=pending-vendors')

@login_required
def reject_vendor_view(request, vendor_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')
    
    try:
        vendor = Vendor.objects.get(id=vendor_id)
        vendor.status = Vendor.Status.REJECTED
        vendor.save()
        
        subject = "ApexStriker - Vendor Application Rejected"
        message = f"Hi {vendor.user.first_name},\n\nWe regret to inform you that your vendor application for '{vendor.shop_name}' has been rejected. If you have any questions or would like to reapply, please contact our support team.\n\nThank you for your interest in ApexStriker."
        threading.Thread(target=send_email_async, args=(subject, message, vendor.user.email)).start()
        
        messages.success(request, f"Vendor '{vendor.shop_name}' has been rejected.")
    except Vendor.DoesNotExist:
        messages.error(request, "Vendor not found.")
    
    return redirect('/dashboard/admin/?section=pending-vendors')

@login_required
def vendor_dashboard_view(request):
    if request.user.role != 'vendor':
        messages.error(request, "You are not authorized to access the vendor dashboard.")
        return redirect('/')
    
    if request.user.vendor_profile.status != 'approved':
        messages.warning(request, "Your vendor account is currently under review. Please wait for approval to access the dashboard.")
        return redirect(f'/profile/{request.user.id}/')
    
    section = request.GET.get('section', 'product-management')
    
    context = {
        'pending_order_count': OrderItem.objects.filter(vendor=request.user.vendor_profile, dispatched=False, order__status='paid').count(),
        'Gross_revenue': sum(item.total_amount for item in Disbursement.objects.filter(vendor=request.user.vendor_profile, is_transferred=True)),
        'Net_revenue': sum(item.payout_amount for item in Disbursement.objects.filter(vendor=request.user.vendor_profile, is_transferred=True)),
        'Admin_commission': sum(item.admin_commission for item in Disbursement.objects.filter(vendor=request.user.vendor_profile, is_transferred=True)),
        'section': section,
    }
    
    if section == 'product-management':
        q = request.GET.get('q', '')
        category = request.GET.get('category', 'all')
        position = request.GET.get('position', 'all')
        sort = request.GET.get('sort', 'latest')
        
        products = Product.objects.filter(vendor=request.user.vendor_profile).order_by('-created_at')
        
        if q:
            query = Q(name__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q) | Q(position__icontains=q) | Q(brand__name__icontains=q)
            products = products.filter(query)
        elif category != 'all':
            products = products.filter(category=category)
        if position != 'all':
            products = products.filter(position=position)
        elif sort == 'oldest':
            products = products.order_by('created_at')
        elif sort == 'price-low-high':
            products = products.order_by('price')
        elif sort == 'price-high-low':
            products = products.order_by('-price')
        elif sort == 'stock-low-high':
            products = products.order_by('stock')
        elif sort == 'stock-high-low':
            products = products.order_by('-stock')
        
        context['products'] = products
        
        
    if section == 'sales-overview':
        context['sales_overview'] = None
        
    if section == 'inventory-management':
        context['inventory'] = None
    
    if section == 'pending-order-items':
        q = request.GET.get('q', '')
        status = request.GET.get('status', 'all')
        sort = request.GET.get('sort', 'latest')
        
        orders = Order.objects.filter(items__vendor=request.user.vendor_profile, status='paid').distinct()
        
        if q:
            query = Q(id__icontains=q) | Q(customer__user__first_name__icontains=q) | Q(customer__user__last_name__icontains=q) | Q(items__product__name__icontains=q) | Q(items__product__brand__name__icontains=q) | Q(items__product__category__icontains=q)
            orders = orders.filter(query).distinct()
            
        if status != 'all' and status == 'pending':
            orders = orders.filter(items__dispatched=False).distinct()
        elif status != 'all' and status == 'dispatched':
            orders = orders.filter(items__dispatched=True).distinct()
        elif status != 'all' and status == 'received':
            orders = orders.filter(items__dispatched=True, items__received=True).distinct()
        elif status != 'all':
            orders = orders.filter(status=status)
            
        if sort == 'latest':
            orders = orders.order_by('-created_at')
        if sort == 'oldest':
            orders = orders.order_by('created_at')
        elif sort == 'price_low':
            orders = orders.order_by('total_amount')
        elif sort == 'price_high':
            orders = orders.order_by('-total_amount')
            
        context['orders'] = orders
                
    return render(request, 'dashboard/vendor_dashboard.html', context)

@login_required
def customer_dashboard_view(request):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized to access the customer dashboard.")
        return redirect('/')
    
    section = request.GET.get('section', 'my-orders')
    
    context = {
        'completed_orders_count': Order.objects.filter(customer=request.user.customer_profile, status='completed').count(),
        'pending_orders_count': Order.objects.filter(customer=request.user.customer_profile, status='paid').count(),
        'wishlist_count': Wishlist.objects.filter(customer=request.user.customer_profile).count(),
        'wishlist_total_amount': sum(item.product.price for item in Wishlist.objects.filter(customer=request.user.customer_profile)),
        'section': section,
    }
    
    if section == 'my-orders':
        q = request.GET.get('q', '')
        status = request.GET.get('status', 'all')
        sort = request.GET.get('sort', 'latest')
        
        orders = Order.objects.filter(customer=request.user.customer_profile).order_by('-created_at')
        
        if q:
            query = Q(id__icontains=q) | Q(items__product__name__icontains=q) | Q(items__product__brand__name__icontains=q) | Q(items__product__category__icontains=q)
            orders = orders.filter(query).distinct()
        
        if status != 'all':
            orders = orders.filter(status=status)
        
        if sort == 'oldest':
            orders = orders.order_by('created_at')
        elif sort == 'amount_desc':
            orders = orders.order_by('-total_amount')
        elif sort == 'amount_asc':
            orders = orders.order_by('total_amount')
            
        context['orders'] = orders

    elif section == 'wishlist':
        context['wishlist'] = Wishlist.objects.filter(customer=request.user.customer_profile).order_by('-added_at')
    
    return render(request, 'dashboard/customer_dashboard.html', context)

def wishlist_remove_view(request, item_id):
    if not request.user.is_authenticated or request.user.role != 'customer':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')

    wishlist_item = Wishlist.objects.filter(id=item_id, customer=request.user.customer_profile).first()
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, "Item removed from your wishlist.")
    else:
        messages.error(request, "Wishlist item not found.")

    return redirect('/dashboard/customer/?section=wishlist')

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