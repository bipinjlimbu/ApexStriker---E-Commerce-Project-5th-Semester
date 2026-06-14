from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Report, User, Cart

def cart_count(request):
    if request.user.is_authenticated and request.user.role == 'customer':
        cart_items_count = Cart.objects.filter(customer=request.user.customer_profile).count()
        return cart_items_count
    return 0

@login_required
def add_report_view(request, user_id):
    return render(request, 'main/add_report_page.html', {'cart_items_count': cart_count(request), 'reported_user_id': user_id})