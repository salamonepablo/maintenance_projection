"""
URLs para módulo de mantenimiento con proyección.
"""
from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_view, name='dashboard'),
    # Proyección de mantenimiento
    path('projection/', views.projection_view, name='projection_view'),
    path('projection/export/', views.projection_export_excel, name='projection_export'),
    path('projection/api/', views.projection_api, name='projection_api'),
]