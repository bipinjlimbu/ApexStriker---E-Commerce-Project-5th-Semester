from django.urls import path
from .views.auth_view import register_view
from .views.main_view import home_view

urlpatterns = [
    path('', home_view, name='home_page'),
    path('register/', register_view, name='register_page'),
]
