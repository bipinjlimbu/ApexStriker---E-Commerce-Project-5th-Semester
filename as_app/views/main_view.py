from django.shortcuts import render
from ..models import User

def home_view(request):
    return render(request, 'main/home_page.html')