"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.urls import path
from .views import planning_view, planning_list, planning_create, planning_delete, planning_validation, planning_detail,define_costing_mapping

app_name = 'planning'

urlpatterns = [
    path('', planning_view, name='planning_view'),
    path("planning/", planning_list, name="planning_list"),
    path("create/", planning_create, name="planning_create"),
    path("<int:pk>/delete/", planning_delete, name="planning_delete"),
    path("<int:pk>/validate/", planning_validation, name="planning_validation"),
    path("<int:pk>/", planning_detail, name="planning_detail"),
    path("<int:pk>/costing-mapping/", define_costing_mapping, name="define_costing_mapping"),
]