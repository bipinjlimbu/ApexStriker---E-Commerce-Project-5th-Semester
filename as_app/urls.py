from django.urls import path
from .views.main_view import home_page

urlpatterns = [
    path('', home_page, name='home_page'),
]
