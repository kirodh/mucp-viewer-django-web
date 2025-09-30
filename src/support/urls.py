"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.urls import path
from .views import support_view, growth_form_list, growth_form_create, growth_form_delete, growth_form_update
from .views import treatment_method_list, treatment_method_create, treatment_method_delete, treatment_method_update
from .views import species_list, species_create, species_edit, species_delete, species_detail
from .views import herbicide_list, herbicide_create, herbicide_delete, herbicide_update
from .views import clearing_norm_list, clearing_norm_create, clearing_norm_delete, clearing_norm_update
from .views import clearing_norm_set_create, clearing_norm_set_delete
from .views import costingmodel_list, costingmodel_create, costingmodel_delete, costingmodel_update
from .views import cost_item_delete_daily, costing_item_add_daily, cost_item_update_daily, costing_item_list_daily
from .views import category_list, category_delete, category_create, category_update
from .views import text_value_create, text_value_delete, text_value_update, text_value_list
from .views import numeric_band_list, numeric_band_create, numeric_band_delete, numeric_band_update

app_name = 'support'

urlpatterns = [
    path('', support_view, name='support_view'),
    # Growth forms
    path('growth-forms/', growth_form_list, name='growth_form_list'),
    path('growth-forms/create/', growth_form_create, name='growth_form_create'),
    path('growth-forms/<int:pk>/edit/', growth_form_update, name='growth_form_update'),
    path('growth-forms/<int:pk>/delete/', growth_form_delete, name='growth_form_delete'),
    # Treatment methods
    path('treatment-method/', treatment_method_list, name='treatment_method_list'),
    path('treatment-method/create/', treatment_method_create, name='treatment_method_create'),
    path('treatment-method/<int:pk>/edit/', treatment_method_update, name='treatment_method_update'),
    path('treatment-method/<int:pk>/delete/', treatment_method_delete, name='treatment_method_delete'),
    # Species
    path('species/', species_list, name='species_list'),
    path('species/add/', species_create, name='species_add'),
    path('species/<int:pk>/edit/', species_edit, name='species_edit'),
    path('species/<int:pk>/delete/', species_delete, name='species_delete'),
    path('species/<int:pk>/', species_detail, name='species_detail'),   # <-- NEW
    # Herbicides
    path('herbicide/', herbicide_list, name='herbicide_list'),
    path('herbicide/create/', herbicide_create, name='herbicide_create'),
    path('herbicide/<int:pk>/edit/', herbicide_update, name='herbicide_update'),
    path('herbicide/<int:pk>/delete/', herbicide_delete, name='herbicide_delete'),
    # Clearing norms
    path('clearing-norm/', clearing_norm_list, name='clearing_norm_list'),
    path('clearing-norm/create/', clearing_norm_create, name='clearing_norm_create'),
    path('clearing-norm/<int:pk>/edit/', clearing_norm_update, name='clearing_norm_update'),
    path('clearing-norm/<int:pk>/delete/', clearing_norm_delete, name='clearing_norm_delete'),
    path('clearing-norm-set/create/', clearing_norm_set_create, name='clearing_norm_set_create'),
    path('clearing-norm-set/<int:pk>/delete/', clearing_norm_set_delete, name='clearing_norm_set_delete'),

    # prioritization model
    path('categories/', category_list, name='category_list'),
    path('categories/add/', category_create, name='category_create'),
    path('categories/<int:pk>/edit/', category_update, name='category_update'),
    path('categories/<int:pk>/delete/', category_delete, name='category_delete'),

    # Numeric Bands
    path('categories/<int:category_id>/numeric_bands/', numeric_band_list, name='numeric_band_list'),
    path('categories/<int:category_id>/numeric_bands/add/', numeric_band_create, name='numeric_band_create'),
    path('numeric_bands/<int:pk>/edit/', numeric_band_update, name='numeric_band_update'),
    path('numeric_bands/<int:pk>/delete/', numeric_band_delete, name='numeric_band_delete'),

    # Text Values
    path('categories/<int:category_id>/text_values/', text_value_list, name='text_value_list'),
    path('categories/<int:category_id>/text_values/add/', text_value_create, name='text_value_create'),
    path('text_values/<int:pk>/edit/', text_value_update, name='text_value_update'),
    path('text_values/<int:pk>/delete/', text_value_delete, name='text_value_delete'),

    # Costing Models
    path('costingmodels/', costingmodel_list, name='costingmodel_list'),
    path('costingmodels/add/', costingmodel_create, name='costingmodel_create'),
    path('costingmodels/<int:pk>/edit/', costingmodel_update, name='costingmodel_update'),
    path('costingmodels/<int:pk>/delete/', costingmodel_delete, name='costingmodel_delete'),
    # Daily Cost Items
    path('costingmodels/<int:costing_model_id>/daily/', costing_item_list_daily, name='dailycost_list'),
    path('costingmodels/<int:costing_model_id>/daily/add/', costing_item_add_daily, name='dailycost_add'),
    path('dailycost/<int:pk>/edit/', cost_item_update_daily, name='dailycost_update'),
    path('dailycost/<int:pk>/delete/', cost_item_delete_daily, name='dailycost_delete'),
]
