from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Product, Brand, Vendor, Cart, Wishlist, Review

def cart_count(request):
    if request.user.is_authenticated and request.user.role == 'customer':
        cart_items_count = Cart.objects.filter(customer=request.user.customer_profile).count()
        return cart_items_count
    return 0

@login_required
def add_review_view(request, product_id):
    if request.user.role != 'customer':
        messages.error(request, "Only customers can submit reviews.")
        return redirect(f'/products/{product_id}/')
    
    if Review.objects.filter(product_id=product_id, customer=request.user.customer_profile).exists():
        messages.error(request, "You have already submitted a review for this product.")
        return redirect(f'/products/{product_id}/')
    
    product = Product.objects.get(id=product_id)
    
    errors = {}
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or int(rating) < 1 or int(rating) > 5:
            errors['rating'] = "Rating must be between 1 and 5."
        
        if not comment:
            errors['comment'] = "Comment cannot be empty."
        
        if errors:
            return render(request, 'main/add_review_page.html', {'cart_count': cart_count(request), 'product': product, 'data': request.POST, 'errors': errors})
        
        review = Review.objects.create(
            product=product,
            customer=request.user.customer_profile,
            rating=rating,
            comment=comment
        )
        review.save()
        
        messages.success(request, "Your review has been submitted successfully.")
        return redirect(f'/products/{product_id}/')
    
    return render(request, 'main/add_review_page.html', {'cart_count': cart_count(request), 'product': product})

@login_required
def edit_review_view(request, review_id):
    review = Review.objects.get(id=review_id)
    
    if review.customer != request.user.customer_profile:
        messages.error(request, "You are not authorized to edit this review.")
        return redirect(f'/products/{review.product.id}/')
    
    errors = {}
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or int(rating) < 1 or int(rating) > 5:
            errors['rating'] = "Rating must be between 1 and 5."
        
        if not comment:
            errors['comment'] = "Comment cannot be empty."
        
        if errors:
            return render(request, 'main/edit_review_page.html', {'cart_count': cart_count(request), 'review': review, 'data': request.POST, 'errors': errors})
        
        review.rating = rating
        review.comment = comment
        review.save()
        
        messages.success(request, "Your review has been updated successfully.")
        return redirect(f'/products/{review.product.id}/')
    
    return render(request, 'main/edit_review_page.html', {'cart_count': cart_count(request), 'review': review})

@login_required
def delete_review_view(request, review_id):
    review = Review.objects.get(id=review_id)
    
    if review.customer != request.user.customer_profile:
        messages.error(request, "You are not authorized to delete this review.")
        return redirect(f'/products/{review.product.id}/')
    
    review.delete()
    messages.success(request, "Your review has been deleted successfully.")
    return redirect(f'/products/{review.product.id}/')