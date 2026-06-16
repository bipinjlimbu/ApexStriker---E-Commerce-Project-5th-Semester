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
    profile = User.objects.get(id=user_id)
    
    if request.user == profile:
        messages.error(request, "You cannot report yourself.")
        return redirect(f'/profile/{profile.id}/')
    
    if Report.objects.filter(reporter=request.user, reported_user=profile).exists():
        messages.error(request, "You have already reported this user.")
        return redirect(f'/profile/{profile.id}/')
    
    errors = {}
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description')
        
        if not reason:
            errors['reason'] = "Reason for reporting is required."
        
        if not description:
            errors['description'] = "Description cannot be empty."
        
        if errors:
            return render(request, 'main/add_report_page.html', {'cart_items_count': cart_count(request), 'profile': profile, 'data': request.POST, 'errors': errors})
        
        report = Report.objects.create(
            reporter=request.user,
            reported_user=profile,
            reason=reason,
            description=description
        )
        report.save()
        
        messages.success(request, "Your report has been submitted successfully.")
        return redirect(f'/profile/{profile.id}/')
    
    return render(request, 'main/add_report_page.html', {'cart_items_count': cart_count(request), 'profile': profile})

@login_required
def resolve_report_view(request, report_id):
    report = Report.objects.get(id=report_id)
    
    if request.user.role != 'admin':
        messages.error(request, "Only admins can resolve reports.")
        return redirect(f'/reports/{report.id}/')
    
    report.is_resolved = True
    report.save()
    
    messages.success(request, "The report has been marked as resolved.")
    return redirect("/dashboard/admin/?section=reported-users")