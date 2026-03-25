from django.shortcuts import render
from django.contrib import messages
from ..models import User

def home_view(request):
    return render(request, 'main/home_page.html')

def verify_email_view(request, token):
    user = None
    status = 'error'
    
    try:
        user = User.objects.get(auth_token=token)
        
        if not user.is_verified:
            user.is_verified = True
            user.auth_token = None  # The "Burn"
            user.save()
            messages.success(request, "Email verification successful!")
        
        status = 'success'
        
    except User.DoesNotExist:
        if request.user.is_authenticated and request.user.is_verified:
            user = request.user
            status = 'success'
        else:
            messages.error(request, "Invalid or expired verification token.")
            status = 'error'
    
    return render(request, 'main/verification_result_page.html', {
        'status': status, 
        'user': user
    })