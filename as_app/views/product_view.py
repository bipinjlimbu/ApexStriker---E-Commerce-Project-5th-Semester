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
    
    return render(request, 'main/add_product_page.html', {'brands': brand})