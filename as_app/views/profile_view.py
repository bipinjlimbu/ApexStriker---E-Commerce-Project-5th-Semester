from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import User

@login_required
def profile_view(request, user_id):
    profile = User.objects.get(id=user_id)
    return render(request, 'main/profile_page.html', {'profile': profile})

@login_required
def edit_profile_view(request, user_id):
    return render(request, 'main/edit_profile_page.html')