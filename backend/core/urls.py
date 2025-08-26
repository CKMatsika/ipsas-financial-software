from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('system-info/', views.system_info, name='system-info'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/', views.export_data, name='export-data'),
    path('import/', views.import_data, name='import-data'),
]
