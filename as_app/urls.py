from django.urls import path
from .views.auth_view import register_view, login_view, logout_view
from .views.main_view import home_view, verify_email_view
from .views.profile_view import profile_view, edit_profile_view, resend_verification_email

urlpatterns = [
    path('', home_view, name='home_page'),
    path('register/', register_view, name='register_page'),
    path('verify/<str:token>/', verify_email_view, name='verify_email'),
    path('login/', login_view, name='login_page'),
    path('logout/', logout_view, name='logout_page'),
    path('profile/<int:user_id>/', profile_view, name='profile_page'),
    path('profile/edit/<int:user_id>/', edit_profile_view, name='edit_profile_page'),
    path('profile/resend_verification/<int:user_id>/', resend_verification_email, name='resend_verification_email'),
]
