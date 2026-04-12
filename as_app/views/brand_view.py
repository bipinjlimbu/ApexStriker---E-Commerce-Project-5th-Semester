from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.core.files.images import get_image_dimensions
from django.conf import settings
from ..models import Brand
import threading

def send_email_async(subject, message, recipient):
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")
            
@login_required
def add_brand_view(request):
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to add a brand.")
        return redirect('home')
    
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
        if logo:
            width, height = get_image_dimensions(logo)
            if width != height:
                errors['logo'] = "Logo must be in 1:1 aspect ratio (square)."
            
        if not description:
            errors['description'] = "Brand description is required."
            
        if not errors:
            brand = Brand.objects.create(name=name, logo=logo, description=description)
            
            subject = "New Brand Added - ApexStriker"
            message = f"Hi {request.user.username},\n\nThe brand '{brand.name}' has been successfully added to ApexStriker.\n\nThank you for contributing to our platform!"
            email_thread = threading.Thread(target=send_email_async, args=(subject, message, request.user.email))
            email_thread.start()

            messages.success(request, f"Brand '{brand.name}' has been added successfully.")
            return redirect('/dashboard/admin/')
        
        return render(request, 'main/add_brand_page.html', {'errors': errors, 'data': request.POST})
    
    return render(request, 'main/add_brand_page.html')