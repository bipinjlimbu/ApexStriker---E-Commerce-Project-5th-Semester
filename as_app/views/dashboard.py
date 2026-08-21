from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Avg
from django.contrib import messages
from ..models import User, Vendor, Brand, Product, Order, OrderItem, Disbursement, Review, Report
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
    brands = Brand.objects.filter(is_active=True).order_by('name')
    
    context = {
        'section' : section,
        'brands': brands,
        'total_pending_vendors': Vendor.objects.filter(status=Vendor.Status.PENDING).count(),
        'total_pending_brands': Brand.objects.filter(is_active=False).count(),
        'total_pending_payouts': Disbursement.objects.filter(is_transferred=False).count(),
        'total_admin_revenue': sum(disbursement.admin_commission for disbursement in Disbursement.objects.filter(is_transferred=True)),
        'total_vendor_revenue': sum(disbursement.payout_amount for disbursement in Disbursement.objects.filter(is_transferred=True)),
        'total_revenue': sum(disbursement.total_amount for disbursement in Disbursement.objects.filter(is_transferred=True)),
        'total_reported_users': Report.objects.filter(is_resolved=False).count(),
        'average_rating': Review.objects.aggregate(average_rating=Avg('rating'))['average_rating'] if Review.objects.exists() else 0,
    }
    
    if section == 'member-list':
        context['members'] = User.objects.exclude(is_superuser=True).order_by('-date_joined')
        
    elif section == 'pending-vendors':
        context['vendors'] = Vendor.objects.filter(status=Vendor.Status.PENDING).order_by('-requested_on')
        
    elif section == 'brand-management':
        context['brands'] = Brand.objects.all()
        
    elif section == 'product-management':
        q = request.GET.get('q', '')
        category = request.GET.get('category', 'all')
        position = request.GET.get('position', 'all')
        brand = request.GET.get('brand', 'all')
        sort = request.GET.get('sort', 'latest')
        
        products = Product.objects.all().order_by('-created_at')
        
        if q:
            query = Q(name__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q) | Q(position__icontains=q) | Q(brand__name__icontains=q)
            products = products.filter(query)
            
        if category != 'all':
            products = products.filter(category=category)
            
        if brand != 'all':
            products = products.filter(brand__id=brand)
            
        if position != 'all':
            products = products.filter(position=position)
            
        if sort == 'oldest':
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
        context['product_reviews'] = Review.objects.all().order_by('-created_at')
        
    elif section == 'revenue-logs':
        context['revenue_logs'] = Disbursement.objects.filter(is_transferred=True).order_by('-created_at')
        
    elif section == 'reported-users':
        context['reported_users'] = Report.objects.all().order_by('-created_at')
        
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def vendor_dashboard_view(request):
    if request.user.role != 'vendor':
        messages.error(request, "You are not authorized to access the vendor dashboard.")
        return redirect('/')
    
    if request.user.vendor_profile.status != 'approved':
        messages.warning(request, "Your vendor account is currently under review. Please wait for approval to access the dashboard.")
        return redirect(f'/profile/{request.user.id}/')
    
    section = request.GET.get('section', 'product-management')
    brands = Brand.objects.filter(is_active=True).order_by('name')
    
    context = {
        'pending_order_count': OrderItem.objects.filter(vendor=request.user.vendor_profile, dispatched=False, order__status='paid').count(),
        'Gross_revenue': sum(item.total_amount for item in Disbursement.objects.filter(vendor=request.user.vendor_profile, is_transferred=True)),
        'Net_revenue': sum(item.payout_amount for item in Disbursement.objects.filter(vendor=request.user.vendor_profile, is_transferred=True)),
        'Admin_commission': sum(item.admin_commission for item in Disbursement.objects.filter(vendor=request.user.vendor_profile, is_transferred=True)),
        'completed_order_items_count': OrderItem.objects.filter(vendor=request.user.vendor_profile, order__status='completed').count(),
        'completed_orders_count': Order.objects.filter(items__vendor=request.user.vendor_profile, status='completed').distinct().count(),
        'average_rating': Review.objects.filter(product__vendor=request.user.vendor_profile).aggregate(average_rating=Avg('rating'))['average_rating'] if Review.objects.filter(product__vendor=request.user.vendor_profile).exists() else 0,
        'section': section,
        'brands': brands,
    }
    
    if section == 'product-management':
        q = request.GET.get('q', '')
        category = request.GET.get('category', 'all')
        position = request.GET.get('position', 'all')
        brand = request.GET.get('brand', 'all')
        sort = request.GET.get('sort', 'latest')
        
        products = Product.objects.filter(vendor=request.user.vendor_profile).order_by('-created_at')
        
        if q:
            query = Q(name__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q) | Q(position__icontains=q) | Q(brand__name__icontains=q)
            products = products.filter(query)
            
        if category != 'all':
            products = products.filter(category=category)
            
        if brand != 'all':
            products = products.filter(brand__id=brand)
            
        if position != 'all':
            products = products.filter(position=position)
            
        if sort == 'oldest':
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
        context['sales_overview'] = Disbursement.objects.filter(vendor=request.user.vendor_profile, is_transferred=True).order_by('-created_at')
        
    if section == 'received-reviews':
        context['received_reviews'] = Review.objects.filter(product__vendor=request.user.vendor_profile).order_by('-created_at')
    
    if section == 'pending-order-items':
        q = request.GET.get('q', '')
        status = request.GET.get('status', 'all')
        sort = request.GET.get('sort', 'latest')
        
        order_items = OrderItem.objects.filter(vendor=request.user.vendor_profile).order_by('-order__created_at')
        
        if q:
            query = Q(order__id__icontains=q) | Q(product__name__icontains=q) | Q(product__brand__name__icontains=q) | Q(product__category__icontains=q)
            order_items = order_items.filter(query).distinct()
            
        if status != 'all' and status == 'pending':
            order_items = order_items.filter(dispatched=False).distinct()   
        elif status != 'all' and status == 'dispatched':
            order_items = order_items.filter(dispatched=True, received=False).distinct()
        elif status != 'all' and status == 'received':
            order_items = order_items.filter(dispatched=True, received=True).distinct()
        elif status != 'all':
            order_items = order_items.filter(status=status)
            
        if sort == 'latest':
            order_items = order_items.order_by('-order__created_at')
        if sort == 'oldest':
            order_items = order_items.order_by('order__created_at')
        elif sort == 'price_low':
            order_items = order_items.order_by('order__total_amount')
        elif sort == 'price_high':
            order_items = order_items.order_by('-order__total_amount')
            
        context['order_items'] = order_items.exclude(order__status='cancelled').exclude(order__status='completed')
        
    if section == 'completed-order-items':            
        context['completed_orders'] = OrderItem.objects.filter(vendor=request.user.vendor_profile, order__status='completed').order_by('-order__created_at')
                
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
        'total_spent': sum(order.total_amount for order in Order.objects.filter(customer=request.user.customer_profile, status='completed')),
        'avg_order_value': Order.objects.filter(customer=request.user.customer_profile, status='completed').aggregate(avg_value=Avg('total_amount'))['avg_value'] if Order.objects.filter(customer=request.user.customer_profile, status='completed').exists() else 0,
        'pending_reports_count': Report.objects.filter(reporter=request.user, is_resolved=False).count(),
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
        
    if section == 'total-spent':
        context['spent_orders'] = Order.objects.filter(customer=request.user.customer_profile, status='completed').order_by('-created_at')
        
    if section == 'my-reviews':
        context['my_reviews'] = Review.objects.filter(customer=request.user.customer_profile).order_by('-created_at')
        
    if section == 'reported-users':
        context['reported_users'] = Report.objects.filter(reporter=request.user).order_by('-created_at')
    
    return render(request, 'dashboard/customer_dashboard.html', context)