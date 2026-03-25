from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard_view(request):
    return render(request, 'dashboard/admin_dashboard.html')

@login_required
def vendor_dashboard_view(request):
    return render(request, 'dashboard/vendor_dashboard.html')

@login_required
def customer_dashboard_view(request):
    return render(request, 'dashboard/customer_dashboard.html')