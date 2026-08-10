from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Wishlist, Product

@login_required
def wishlist_view(request):
    return render(request, 'main/wishlist_page.html')

@login_required
def wishlist_toggle_view(request, product_id):
    if not request.user.is_authenticated or request.user.role != 'customer':
        messages.error(request, "You must be logged in as a customer to manage your wishlist.")
        return redirect('/login/')
    
    product = Product.objects.get(id=product_id)
    wishlist_item = Wishlist.objects.filter(customer=request.user.customer_profile, product=product).first()
    
    if wishlist_item:
        wishlist_item.delete()
        messages.info(request, f"'{product.name}' has been removed from your wishlist.")
    else:
        Wishlist.objects.create(customer=request.user.customer_profile, product=product)
        messages.success(request, f"'{product.name}' has been added to your wishlist.")
    
    return redirect(f'/products/{product_id}/')

@login_required
def wishlist_remove_view(request, item_id):
    if not request.user.is_authenticated or request.user.role != 'customer':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('/')

    wishlist_item = Wishlist.objects.filter(id=item_id, customer=request.user.customer_profile).first()
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, "Item removed from your wishlist.")
    else:
        messages.error(request, "Wishlist item not found.")

    return redirect('/wishlist/')