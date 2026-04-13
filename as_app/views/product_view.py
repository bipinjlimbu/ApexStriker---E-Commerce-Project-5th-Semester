from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Product, Brand, Vendor

@login_required
def add_product_view(request):
    if request.user.role != 'vendor' and not Vendor.objects.filter(user=request.user, status=Vendor.Status.APPROVED).exists():
        messages.error(request, "You are not authorized to add products.")
        return redirect('/')
    
    brand = Brand.objects.all()
    
    errors = {}
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category = request.POST.get('category')
        brand_id = request.POST.get('brand')
        images = request.FILES.getlist('images')
        
        if not name:
            errors['name'] = "Product name is required."
            
        if not description:
            errors['description'] = "Product description is required."
            
        if not price or float(price) <= 0:
            errors['price'] = "Price must be a positive number."
            
        if not stock or int(stock) < 0:
            errors['stock'] = "Stock must be a non-negative integer."
            
        if not category:
            errors['category'] = "Category selection is required."
            
        if not brand_id:
            errors['brand'] = "Brand selection is required."
            
        if len(images) == 0:
            errors['images'] = "At least one image is required."
        if len(images) > 5:
            errors['images'] = "You can upload a maximum of 5 images."

        if errors:
            return render(request, 'main/add_product_page.html', { 'brands': brand, 'data': request.POST, 'errors': errors })
        
        brand_instance = Brand.objects.get(id=brand_id)
        
        product = Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            brand=brand_instance,
            vendor=request.user.vendor_profile
        )
        
        for image in images:
            product.images.create(image=image)
        
        messages.success(request, f"Product '{product.name}' has been added successfully.")
        return redirect('/dashboard/vendor/')
    
    return render(request, 'main/add_product_page.html', {'brands': brand})

def marketplace_view(request):
    return render(request, 'main/marketplace_page.html')