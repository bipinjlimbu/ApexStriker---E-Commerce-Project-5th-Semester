from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..models import User, Vendor
import uuid
import threading

@login_required
def profile_view(request, user_id):
    profile = User.objects.get(id=user_id)
    return render(request, 'main/profile_page.html', {'profile': profile})

@login_required
def resend_verification_email(request, user_id):
    user = User.objects.get(id=user_id)
    if user.is_verified:
        messages.info(request, "Your email is already verified.")
        return redirect(f'/profile/{user_id}/')
    
    def send_email_async(subject, message, recipient):
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")
    
    auth_token = str(uuid.uuid4())
    user.auth_token = auth_token
    user.save()
    
    verify_url = f"http://127.0.0.1:8000/verify/{auth_token}/"
    subject = "ApexStriker - Verify Your Email"
    message = f"Hi {user.username},\n\nPlease click the link below to verify your email:\n\n{verify_url} \n\nThank you for being a part of ApexStriker!"
    
    threading.Thread(target=send_email_async, args=(subject, message, user.email)).start()
    
    messages.success(request, "A new verification email has been sent. Please check your inbox.")
    return redirect(f'/profile/{user_id}/')

@login_required
def edit_profile_view(request, user_id):
    if request.user.id != user_id:
        messages.error(request, "You are not authorized to edit this profile.")
        return redirect(f'/profile/{user_id}/')
    
    user = User.objects.get(id=user_id)
    vendor = user.vendor_profile if user.role == User.Role.VENDOR else None
    customer = user.customer_profile if user.role == User.Role.CUSTOMER else None
    
    errors = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        shipping_address = request.POST.get('shipping_address')
        city = request.POST.get('city')
        position = request.POST.get('position')
        shop_name = request.POST.get('shop_name')
        shop_address = request.POST.get('shop_address')
        pan_number = request.POST.get('pan_number')
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
            if not city:
                errors['city'] = "City is required for customers."
        
        if user.role == User.Role.VENDOR:
            if not shop_name:
                errors['shop_name'] = "Shop name is required for vendors."
            if not shop_address:
                errors['shop_address'] = "Shop address is required for vendors."
            if not pan_number:
                errors['pan_number'] = "PAN number is required for vendors."
            if not city:
                errors['city'] = "City is required for vendors."
            if not bank_account_number:
                errors['bank_account_number'] = "Bank account number is required for vendors."
                              
        if errors:
            return render(request, 'main/edit_profile_page.html', { 'user': user, 'data': request.POST, 'errors': errors })
        
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        if profile_picture:
            user.profile_picture = profile_picture
        user.save()
        
        if user.role == User.Role.CUSTOMER:
            customer.shipping_address = shipping_address
            customer.city = city
            customer.position = position
            customer.save()
            
        elif user.role == User.Role.VENDOR:
            vendor.shop_name = shop_name
            vendor.shop_address = shop_address
            vendor.city = city
            vendor.pan_number = pan_number
            if vendor.bank_account_number != bank_account_number:
                vendor.bank_account_number = bank_account_number
                vendor.status = Vendor.Status.PENDING
                messages.warning(request, "Changes to bank account number require re-verification. Your vendor status has been set to pending until verification is complete.")
            vendor.save()
            
        messages.success(request, "Profile updated successfully.")
        return redirect(f'/profile/{user.id}/')
        
    return render(request, 'main/edit_profile_page.html',{"user": user})

