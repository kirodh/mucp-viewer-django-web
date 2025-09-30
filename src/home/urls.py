"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home_view'),
    path('register/', views.register, name='register'),
    path("contact/", views.contact_us, name="contact_us"),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
]
