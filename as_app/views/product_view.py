from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Case, When, Value, IntegerField
from ..models import Product, Brand, Vendor
import json

@login_required
def add_product_view(request):
    if request.user.role != 'vendor' and not Vendor.objects.filter(user=request.user, status=Vendor.Status.APPROVED).exists():
        messages.error(request, "You are not authorized to add products.")
        return redirect('/')
    
    brand = Brand.objects.filter(is_active=True).order_by('created_at')
    
    errors = {}
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category = request.POST.get('category')
        brand_id = request.POST.get('brand')
        images = request.FILES.getlist('images')
        position = request.POST.get('position')
        primary_image = request.POST.get('primary_image_name')
        
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
            vendor=request.user.vendor_profile,
            position=position
        )
        
        for image in images:
            is_primary = (image.name == primary_image)
            
            if is_primary:
                product.images.create(image=image, is_primary=True)
            else:
                product.images.create(image=image)
        
        messages.success(request, f"Product '{product.name}' has been added successfully.")
        return redirect('/dashboard/vendor/')
    
    return render(request, 'main/add_product_page.html', {'brands': brand})

def marketplace_view(request):
    context = {}

    query = request.GET.get('q')
    category = request.GET.get('category', 'all')
    brand_id = request.GET.get('brand', 'all')
    price_range = request.GET.get('price', 'all')
    sort = request.GET.get('sort', 'recommended')

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(brand__name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )

    if category and category != 'all':
        products = products.filter(category=category)

    if brand_id and brand_id != 'all':
        products = products.filter(brand_id=brand_id)
        
    if price_range and price_range != 'all':
        if price_range == 'under_5000':
            products = products.filter(price__lt=5000)
        elif price_range == '5000_15000':
            products = products.filter(price__gte=5000, price__lte=15000)
        elif price_range == '15000_30000':
            products = products.filter(price__gte=15000, price__lte=30000)
        elif price_range == 'over_30000':
            products = products.filter(price__gt=30000)

    if sort == 'recommended':
        position = request.user.customer_profile.position if hasattr(request.user, 'customer_profile') else None
        if position:
            products = products.annotate(
                priority=Case(
                    When(position=position, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField()
                )
            ).order_by('priority', '-created_at')
        else:
            products = products.order_by('-created_at')
            
    elif sort == 'price_low_high':
        products = products.order_by('price')
    elif sort == 'price_high_low':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')
        
    position = request.user.customer_profile.position if hasattr(request.user, 'customer_profile') else None

    if position:
        recommended = Product.objects.filter(position=position).order_by('-created_at')
        context['recommended_products'] = recommended
        
    context['products'] = products
    context['brands'] = Brand.objects.filter(is_active=True).order_by('created_at')
    
    return render(request, 'main/marketplace_page.html', context)

@login_required
def edit_product_view(request, product_id):
    if request.user.role != 'vendor' and not Vendor.objects.filter(user=request.user, is_active=True).exists():
        messages.error(request, "You are not authorized to edit products.")
        return redirect('/')
    
    brands = Brand.objects.filter(is_active=True).order_by('created_at')
    product = Product.objects.get(id=product_id)
    print(product.position)
    
    errors = {}
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category = request.POST.get('category')
        brand_id = request.POST.get('brand')
        position = request.POST.get('position')
        
        new_images = request.FILES.getlist('images')
        primary_image = request.POST.get('primary_image_name')
        keep_existing_json = request.POST.get('keep_existing','[]')
        keep_existing_names = json.loads(keep_existing_json)
        
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
            
        total_images = len(new_images) + len(keep_existing_names)
        if total_images == 0:
            errors['images'] = "At least one image is required."
        if total_images > 5:
            errors['images'] = "You can upload a maximum of 5 images."

        if errors:
            return render(request, 'main/add_product_page.html', { 'brands': brands,'product': product, 'data': request.POST, 'errors': errors })
        
        brand_instance = Brand.objects.get(id=brand_id)
        
        product.name = name
        product.description = description
        product.price = price
        product.stock = stock
        product.brand = brand_instance
        product.position = position
        product.save()
        
        product.images.exclude(image__in=keep_existing_names).delete()
        product.images.all().update(is_primary=False)
        existing_primary = product.images.filter(image=primary_image).first()
        
        if existing_primary:
            existing_primary.is_primary = True
            existing_primary.save()
            
        for image in new_images:
            is_primary = (image.name == primary_image)
            
            if existing_primary:
                is_primary = False
                
            product.images.create(image=image, is_primary=is_primary)
                    
        messages.success(request, f"Product '{product.name}' has been updated successfully.")
        return redirect('/dashboard/vendor/')
        
    return render(request, 'main/edit_product_page.html', {'brands': brands, 'product': product})

@login_required
def delete_product_view(request, product_id):
    if request.user.role != 'vendor' and not Vendor.objects.filter(user=request.user, is_active=True).exists():
        messages.error(request, "You are not authorized to delete products.")
        return redirect('/')
    
    product = Product.objects.get(id=product_id)
    product_name = product.name
    product.delete()
    
    messages.success(request, f"Product '{product_name}' has been deleted successfully.")
    return redirect('/dashboard/vendor/')