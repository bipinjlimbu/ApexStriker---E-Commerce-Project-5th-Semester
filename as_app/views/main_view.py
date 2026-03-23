from django.shortcuts import render

def home_view(request):
    return render(request, 'main/home_page.html')

def profile_view(request):
    return render(request, 'main/profile_page.html')