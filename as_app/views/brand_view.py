from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Brand

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
            
        if not description:
            errors['description'] = "Brand description is required."
            
        if not errors:
            brand = Brand.objects.create(name=name, logo=logo, description=description)
            messages.success(request, f"Brand '{brand.name}' has been added successfully.")
            return redirect('/brands/')
        
        return render(request, 'main/add_brand_page.html', {'errors': errors, 'data': request.POST})
    
    return render(request, 'main/add_brand_page.html')