"""
URL configuration for IPSAS Financial Software project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/chart-of-accounts/', include('chart_of_accounts.urls')),
    path('api/journal-entries/', include('journal_entries.urls')),
    path('api/financial-statements/', include('financial_statements.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/audit-trail/', include('audit_trail.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
