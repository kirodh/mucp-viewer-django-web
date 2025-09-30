"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
# project/urls.py
from django.urls import path, include
from .views import project_view, project_list, project_create, project_detail, project_delete
app_name = 'project'

urlpatterns = [
    path('', project_view, name='project_view'),
    path('project', project_list, name='project_list'),
    path('create/', project_create, name='project_create'),
    path('<int:pk>/', project_detail, name='project_detail'),
    path('<int:pk>/delete/', project_delete, name='project_delete'),
]

