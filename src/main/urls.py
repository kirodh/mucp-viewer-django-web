"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

MUCP TOOL
Author: Kirodh Boodhraj

"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # adds login, logout, password_change, etc.
    # path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    # path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    # path('accounts/', include('home.urls', namespace='home')),  # registration
    path('', include('home.urls', namespace='home')),
    # path('', include('home.urls')),
    path('planning/', include('planning.urls', namespace='planning')),
    path('support/', include('support.urls', namespace='support')),
    path('project/', include('project.urls', namespace='project')),
    path('visualization/', include('visualization.urls', namespace='visualization')),
]
