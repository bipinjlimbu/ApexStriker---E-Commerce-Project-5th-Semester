from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..models import Brand, Cart
import threading

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
            
def brands_view(request):
    brands = Brand.objects.all()
    return render(request, 'main/brands_page.html', {'brands': brands, 'cart_count': cart_count(request)})
            
@login_required
def add_brand_view(request):
    if request.user.role == 'customer':
        messages.error(request, "You are not authorized to add a brand.")
        return redirect('/brands/')
    
    errors = {}
    if request.method == 'POST':
        name = request.POST.get('name')
        logo = request.FILES.get('logo')
        description = request.POST.get('description')
        
        if not name:
            errors['name'] = "Brand name is required."
        elif Brand.objects.filter(name=name).exists():
            errors['name'] = "A brand with this name already exists."
            
        if not logo:
            errors['logo'] = "Brand logo is required."
            
        if not description:
            errors['description'] = "Brand description is required."
            
        if not errors:
            brand = Brand.objects.create(name=name, logo=logo, description=description)
            
            if request.user.role == 'admin':
                brand.is_active = True
                brand.save()
            
                subject = "New Brand Added - ApexStriker"
                message = f"Hi {request.user.username},\n\nThe brand '{brand.name}' has been successfully added to ApexStriker.\n\nThank you for contributing to our platform!"
                email_thread = threading.Thread(target=send_email_async, args=(subject, message, request.user.email))
                email_thread.start()

                messages.success(request, f"Brand '{brand.name}' has been added successfully.")
                return redirect('/dashboard/admin/?section=brand-management')
            
            subject = "Brand Submission Received - ApexStriker"
            message = f"Hi {request.user.username},\n\nThank you for submitting the brand '{brand.name}' to ApexStriker. Your submission is currently under review by our team. We will notify you once it has been approved and added to our platform.\n\nThank you for contributing to our community!"
            email_thread = threading.Thread(target=send_email_async, args=(subject, message, request.user.email))
            email_thread.start()
            
            messages.success(request, f"Brand '{brand.name}' has been submitted successfully and is pending approval.")
            return redirect('/brands/')
        
        return render(request, 'main/add_brand_page.html', {'errors': errors, 'data': request.POST, 'cart_count': cart_count(request)})
    
    return render(request, 'main/add_brand_page.html', {'cart_count': cart_count(request)})

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
def edit_brand_view(request, brand_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to edit a brand.")
        return redirect('/brands/')
    
    errors = {}
    
    brand = Brand.objects.filter(id=brand_id).first()
    
    if not brand:
        messages.error(request, "Brand not found.")
        return redirect('/dashboard/admin/?section=brand-management')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        logo = request.FILES.get('logo')
        description = request.POST.get('description')
        
        if not logo:
            logo = brand.logo
            
        if not name:
            errors['name'] = "Brand name is required."
        elif Brand.objects.filter(name=name).exclude(id=brand_id).exists():
            errors['name'] = "A brand with this name already exists."
            
        if not description:
            errors['description'] = "Brand description is required."
            
        if not errors:
            brand = Brand.objects.get(id=brand_id)
            brand.name = name
            brand.logo = logo
            brand.description = description
            brand.save()
            
            subject = "Brand Updated - ApexStriker"
            message = f"Hi {request.user.username},\n\nThe brand '{brand.name}' has been successfully updated on ApexStriker.\n\nThank you for keeping our platform up-to-date!"
            email_thread = threading.Thread(target=send_email_async, args=(subject, message, request.user.email))
            email_thread.start()

            messages.success(request, f"Brand '{brand.name}' has been updated successfully.")
            return redirect('/dashboard/admin/?section=brand-management')
        
        return render(request, 'main/edit_brand_page.html', {'errors': errors, 'data': request.POST, 'brand': brand, 'cart_count': cart_count(request)})
    
    return render(request, 'main/edit_brand_page.html', {'brand': brand, 'cart_count': cart_count(request)})

@login_required
def delete_brand_view(request, brand_id):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to delete a brand.")
        return redirect('/brands/')
    
    brand = Brand.objects.filter(id=brand_id).first()
    
    if not brand:
        messages.error(request, "Brand not found.")
        return redirect('/dashboard/admin/?section=brand-management')
    
    brand_name = brand.name
    brand.delete()
    
    subject = "Brand Deleted - ApexStriker"
    message = f"Hi {request.user.username},\n\nThe brand '{brand_name}' has been successfully deleted from ApexStriker.\n\nThank you for managing our platform!"
    email_thread = threading.Thread(target=send_email_async, args=(subject, message, request.user.email))
    email_thread.start()

    messages.success(request, f"Brand '{brand_name}' has been deleted successfully.")
    return redirect('/dashboard/admin/?section=brand-management')