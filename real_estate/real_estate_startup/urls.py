from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('properties/', views.property_list, name='property_list'),
    path('property/<int:property_id>/', views.property_detail, name='property_detail'),
    path('property/<int:property_id>/inquiry/', views.submit_inquiry, name='submit_inquiry'),
    path('property/<int:property_id>/save/', views.toggle_save_property, name='toggle_save_property'),
    path('saved-properties/', views.saved_properties, name='saved_properties'),
]
