from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Brand

@login_required
def add_brand_view(request):
    return render(request, 'main/add_brand_page.html')