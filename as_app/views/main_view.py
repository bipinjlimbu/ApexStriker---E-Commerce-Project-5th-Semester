from django.shortcuts import render
from ..models import User

def home_view(request):
    return render(request, 'main/home_page.html')

def profile_view(request):
    profile = User.objects.get(id=request.user.id)
    return render(request, 'main/profile_page.html', {'profile': profile})