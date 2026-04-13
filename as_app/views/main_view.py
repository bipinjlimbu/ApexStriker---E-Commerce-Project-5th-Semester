from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from ..models import User, Product, Brand
import threading
import uuid

def send_email_async(subject, message, recipient):
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")
            
def home_view(request):
    context = {}
    
    context['products'] = Product.objects.all().order_by('-created_at')[:5]
    
    context['brands'] = Brand.objects.filter(is_active=True).order_by('created_at')[:4]
    
    return render(request, 'main/home_page.html', context)

def verify_email_view(request, token):
    user = None
    status = 'error'
    
    try:
        user = User.objects.get(auth_token=token)
        
        if not user.is_verified:
            user.is_verified = True
            user.auth_token = None
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
    
def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            reset_token = str(uuid.uuid4())
            user.auth_token = reset_token
            user.save()
            
            reset_url = f"http://127.0.0.1:8000/password-reset/{reset_token}/"
            
            subject = "ApexStriker - Password Reset Request"
            message = f"Hi {user.first_name},\n\nWe received a request to reset your password. Please click the link below to set a new password:\n\n{reset_url}\n\nIf you did not request a password reset, please ignore this email.\n\nThank you for being a part of ApexStriker!"
            threading.Thread(target=send_email_async, args=(subject, message, user.email)).start()

            messages.success(request, "If an account with that email exists, a password reset link has been sent.")
        except User.DoesNotExist:
            messages.success(request, "If an account with that email exists, a password reset link has been sent.")
    return render(request, 'main/password_reset_page.html')

def password_reset_confirm_view(request, token):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'main/password_reset_confirm_page.html')
        
        try:
            user = User.objects.get(auth_token=token)
            user.set_password(password)
            user.auth_token = None
            user.save()
            
            messages.success(request, "Your password has been reset successfully. You can now log in with your new password.")
            return redirect('/login/')
        except User.DoesNotExist:
            messages.error(request, "Invalid or expired password reset token.")
            return render(request, 'main/password_reset_confirm_page.html')
        
    return render(request, 'main/password_reset_confirm_page.html')