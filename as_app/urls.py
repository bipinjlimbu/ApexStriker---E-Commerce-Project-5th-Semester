from django.urls import path
from .views.auth_view import register_view, login_view
from .views.main_view import home_view

urlpatterns = [
    path('', home_view, name='home_page'),
    path('register/', register_view, name='register_page'),
    path('login/', login_view, name='login_page'),
]
