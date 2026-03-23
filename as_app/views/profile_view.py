from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import User, Vendor, Customer

@login_required
def profile_view(request, user_id):
    profile = User.objects.get(id=user_id)
    return render(request, 'main/profile_page.html', {'profile': profile})

@login_required
def edit_profile_view(request, user_id):
    if request.user.id != user_id:
        messages.error(request, "You are not authorized to edit this profile.")
        return render(request, 'main/profile_page.html', {'profile': request.user})
    
    user = User.objects.get(id=user_id)
    
    errors = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        shipping_address = request.POST.get('shipping_address')
        city_customer = request.POST.get('city_customer')
        position = request.POST.get('position')
        shop_name = request.POST.get('shop_name')
        shop_address = request.POST.get('shop_address')
        pan_number = request.POST.get('pan_number')
        city_vendor = request.POST.get('city_vendor')
        bank_account_number = request.POST.get('bank_account_number')
        profile_picture = request.FILES.get('profile_picture')
        
        if not username:
            errors['username'] = "Username is required."
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            errors['username'] = "Username already exists."
            
        if not first_name:
            errors['first_name'] = "First name is required."
        if not last_name:
            errors['last_name'] = "Last name is required."
            
        if not email:
            errors['email'] = "Email is required."
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            errors['email'] = "Email already exists."
            
        if user.role == User.Role.CUSTOMER:
            if not shipping_address:
                errors['shipping_address'] = "Shipping address is required for customers."
            if not city_customer:
                errors['city_customer'] = "City is required for customers."
        
        if user.role == User.Role.VENDOR:
            if not shop_name:
                errors['shop_name'] = "Shop name is required for vendors."
            if not shop_address:
                errors['shop_address'] = "Shop address is required for vendors."
            if not pan_number:
                errors['pan_number'] = "PAN number is required for vendors."
            if not city_vendor:
                errors['city_vendor'] = "City is required for vendors."
            if not bank_account_number:
                errors['bank_account_number'] = "Bank account number is required for vendors."
                              
        if not errors:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.phone = phone
            if profile_picture:
                user.profile_picture = profile_picture
            user.save()
            
            if user.role == User.Role.CUSTOMER:
                user.customer_profile.shipping_address = shipping_address
                user.customer_profile.city = city_customer
                user.customer_profile.position = position
                user.customer_profile.save()
                
            elif user.role == User.Role.VENDOR:
                user.vendor_profile.shop_name = shop_name
                user.vendor_profile.shop_address = shop_address
                user.vendor_profile.city = city_vendor
                user.vendor_profile.pan_number = pan_number
                if user.vendor_profile.bank_account_number != bank_account_number:
                    user.vendor_profile.bank_account_number = bank_account_number
                    user.vendor_profile.status = Vendor.Status.PENDING
                    messages.warning(request, "Changes to bank account number require re-verification. Your vendor status has been set to pending until verification is complete.")
                user.vendor_profile.save()
                
            messages.success(request, "Profile updated successfully.")
            return redirect(f'/profile/{user.id}/')
        
        return render(request, 'main/edit_profile_page.html', { 'user': user, 'data': request.POST, 'errors': errors })

    return render(request, 'main/edit_profile_page.html',{'user': user})