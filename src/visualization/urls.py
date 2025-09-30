"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.urls import path
from .views import visualization_home, visualization_view, visualization_selector, visualization_data, visualization_timeseries, visualization_pdf, map_data

app_name = 'visualization'

urlpatterns = [
    path('', visualization_home, name='visualization_view'),
]


urlpatterns += [
    path('selector/', visualization_selector, name='visualization_selector'),
    path('view/<int:planning_id>/', visualization_view, name='visualization_view'),
    path('data/<int:planning_id>/', visualization_data, name='visualization_data'),
    path('map_data/<int:planning_id>/', map_data, name='map_data'),
    path('timeseries/<int:planning_id>/', visualization_timeseries, name='visualization_timeseries'),
    path('pdf/<int:planning_id>/<int:year>/<str:budget>/', visualization_pdf, name='visualization_pdf'),
]
