from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import User, Vendor

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
        messages.success(request, f"Vendor '{vendor.shop_name}' has been approved successfully.")
    except Vendor.DoesNotExist:
        messages.error(request, "Vendor not found.")
    
    return redirect('/dashboard/?section=pending-vendors')

@login_required
def vendor_dashboard_view(request):
    if request.user.role != 'vendor':
        messages.error(request, "You are not authorized to access the vendor dashboard.")
        return redirect('/')
    
    if request.user.vendor_profile.status != 'approved':
        messages.warning(request, "Your vendor account is currently under review. Please wait for approval to access the dashboard.")
        return redirect(f'/profile/{request.user.id}/')
    
    return render(request, 'dashboard/vendor_dashboard.html')

@login_required
def customer_dashboard_view(request):
    if request.user.role != 'customer':
        messages.error(request, "You are not authorized to access the customer dashboard.")
        return redirect('/')
    
    return render(request, 'dashboard/customer_dashboard.html')