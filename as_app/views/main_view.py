from django.shortcuts import render
from django.contrib import messages
from ..models import User

def home_view(request):
    return render(request, 'main/home_page.html')

def verify_email_view(request, token):
    try:
        user = User.objects.get(auth_token=token)
        if user.is_verified:
            messages.info(request, "Your email is already verified.")
        else:
            user.is_verified = True
            user.auth_token = None
            user.save()
            messages.success(request, "Email verification successful! You can now log in.")
    except User.DoesNotExist:
        messages.error(request, "Invalid verification token.")
    
    return render(request, 'main/verification_result_page.html', {'status': 'success' if user.is_verified else 'error', 'user': user})