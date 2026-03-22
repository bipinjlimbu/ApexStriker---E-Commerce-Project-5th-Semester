from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from ..models import User, Vendor, Customer

def register_view(request):
    errors = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        shipping_address = request.POST.get('shipping_address')
        city_customer = request.POST.get('city_customer')
        position = request.POST.get('position')
        shop_name = request.POST.get('shop_name')
        shop_address = request.POST.get('shop_address')
        pan_number = request.POST.get('pan_number')
        city_vendor = request.POST.get('city_vendor')
        bank_account_number = request.POST.get('bank_account_number')
        id_proof = request.FILES.get('id_proof')
        profile_picture = request.FILES.get('profile_picture')
        
        if not username:
            errors['username'] = "Username is required."
        if User.objects.filter(username=username).exists():
            errors['username'] = "Username already exists."
            
        if not first_name:
            errors['first_name'] = "First name is required."
        if not last_name:
            errors['last_name'] = "Last name is required."
            
        if not email:
            errors['email'] = "Email is required."
        if User.objects.filter(email=email).exists():
            errors['email'] = "Email already exists."
            
        if not password:
            errors['password'] = "Password is required."
        if password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."
            
        if role == 'customer':
            if not shipping_address:
                errors['shipping_address'] = "Shipping address is required for customers."
            if not city_customer:
                errors['city_customer'] = "City is required for customers."
        
        if role == 'vendor':
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
            if not id_proof:
                errors['id_proof'] = "ID proof is required for vendors."
                
        if not errors:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        password=password,
                        role=role,
                        phone=phone,
                        profile_picture=profile_picture if profile_picture else None
                    )
                    if role == 'customer':
                        Customer.objects.create(
                            user=user,
                            shipping_address=shipping_address,
                            city=city_customer,
                            position=position if position else None
                        )
                    elif role == 'vendor':
                        Vendor.objects.create(
                            user=user,
                            shop_name=shop_name,
                            shop_address=shop_address,
                            pan_number=pan_number,
                            city=city_vendor,
                            bank_account_number=bank_account_number,
                            id_proof=id_proof,
                            status=Vendor.Status.PENDING
                        )
                    messages.success(request, "Registration successful!")
                    return redirect('/login/')
            except Exception as e:
                print("Error during registration:", e)
                messages.error(request, "An error occurred during registration. Please try again.")
        
        return render(request, 'auth/register_page.html', {'errors': errors,'data': request.POST})

    return render(request, 'auth/register_page.html')

def login_view(request):
    errors = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember') == 'on'
        
        if not username:
            errors['username'] = "Username is required."
        if not password:
            errors['password'] = "Password is required."
        
        if not errors:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if remember:
                    request.session.set_expiry(1209600)
                else:
                    request.session.set_expiry(0) 
                messages.success(request, f"Login successful!Welcome back, {user.first_name}!")
                return redirect('/')
            else:
                messages.error(request, "Invalid username or password.")
                return render(request, 'auth/login_page.html', {'errors': errors,'data': request.POST})
                
        return render(request, 'auth/login_page.html', {'errors': errors,'data': request.POST})
            
    return render(request, 'auth/login_page.html')