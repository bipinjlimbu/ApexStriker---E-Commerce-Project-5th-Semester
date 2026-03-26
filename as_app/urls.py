from django.urls import path
from .views.auth_view import register_view, login_view, logout_view
from .views.main_view import home_view, verify_email_view, password_reset_view
from .views.profile_view import profile_view, edit_profile_view, resend_verification_email, delete_profile_view
from .views.dashboard import admin_dashboard_view, approve_vendor_view, reject_vendor_view, vendor_dashboard_view, customer_dashboard_view

urlpatterns = [
    path('', home_view, name='home_page'),
    path('register/', register_view, name='register_page'),
    path('verify/<str:token>/', verify_email_view, name='verify_email'),
    path('password-reset/', password_reset_view, name='password_reset_page'),
    path('login/', login_view, name='login_page'),
    path('logout/', logout_view, name='logout_page'),
    path('profile/<int:user_id>/', profile_view, name='profile_page'),
    path('profile/edit/<int:user_id>/', edit_profile_view, name='edit_profile_page'),
    path('profile/resend_verification/<int:user_id>/', resend_verification_email, name='resend_verification_email'),
    path('profile/delete/<int:user_id>/', delete_profile_view, name='delete_profile_page'),
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),
    path('approve_vendor/<int:vendor_id>/', approve_vendor_view, name='approve_vendor'),
    path('reject_vendor/<int:vendor_id>/', reject_vendor_view, name='reject_vendor'),
    path('dashboard/vendor/', vendor_dashboard_view, name='vendor_dashboard'),
    path('dashboard/customer/', customer_dashboard_view, name='customer_dashboard'),
]
