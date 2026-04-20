from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from ..models import User, Vendor, Brand, Product, Order, Wishlist
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
        'total_products_reviews': 350,
    }
    
    if section == 'member-list':
        context['members'] = User.objects.all().order_by('-date_joined')
        
    elif section == 'pending-vendors':
        context['vendors'] = Vendor.objects.filter(status=Vendor.Status.PENDING).order_by('-requested_on')
        
    elif section == 'brand-management':
        context['brands'] = Brand.objects.all()
        
    elif section == 'product-reviews':
        context['product-reviews'] = None
        
    elif section == 'revenue-logs':
        context['revenue-logs'] = None

    
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
def approve_brand_view(request, brand_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')
    
    try:
        brand = Brand.objects.get(id=brand_id)
        brand.is_active = True
        brand.save()
        
        subject = "ApexStriker - Brand Approved"
        message = f"Hi {request.user.first_name},\n\nThe brand '{brand.name}' has been approved and is now live on ApexStriker. Thank you for contributing to our platform!"
        threading.Thread(target=send_email_async, args=(subject, message, request.user.email)).start()
        
        messages.success(request, f"Brand '{brand.name}' has been approved successfully.")
    except Brand.DoesNotExist:
        messages.error(request, "Brand not found.")
    
    return redirect('/dashboard/admin/?section=brand-management')

@login_required
def delete_brand_view(request, brand_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')
    
    try:
        brand = Brand.objects.get(id=brand_id)
        brand.delete()
        
        subject = "ApexStriker - Brand Deleted"
        message = f"Hi {request.user.first_name},\n\nThe brand '{brand.name}' has been deleted from ApexStriker. If you have any questions, please contact our support team.\n\nThank you."
        threading.Thread(target=send_email_async, args=(subject, message, request.user.email)).start()
        
        messages.success(request, f"Brand '{brand.name}' has been deleted successfully.")
    except Brand.DoesNotExist:
        messages.error(request, "Brand not found.")
    
    return redirect('/dashboard/admin/?section=brand-management')

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
        'pending_orders': None,
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
    
    if section == 'pending-orders':
        context['orders'] = None
        
    return render(request, 'dashboard/vendor_dashboard.html', context)

@login_required
def customer_dashboard_view(request):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized to access the customer dashboard.")
        return redirect('/')
    
    section = request.GET.get('section', 'my-orders')
    
    context = {
        'orders': None,
        'wishlist': None,
        'section': section,
    }
    
    if section == 'my-orders':
        context['orders'] = Order.objects.filter(customer=request.user.customer_profile).order_by('-created_at')
        
    elif section == 'wishlist':
        context['wishlist'] = Wishlist.objects.filter(customer=request.user.customer_profile).order_by('-added_at')
    
    return render(request, 'dashboard/customer_dashboard.html', context)