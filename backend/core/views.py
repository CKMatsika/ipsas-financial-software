from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.conf import settings
from django.utils import timezone
import psutil
import os


@api_view(['GET'])
def health_check(request):
    """System health check endpoint."""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
            }
        }
        
        return Response(health_status)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_info(request):
    """Get system information and configuration."""
    system_info = {
        'django_version': '4.2.7',
        'python_version': '3.8+',
        'database': settings.DATABASES['default']['ENGINE'],
        'ipsas_version': getattr(settings, 'IPSAS_VERSION', '2022'),
        'zimbabwe_compliance': getattr(settings, 'ZIMBABWE_COMPLIANCE', True),
        'fiscal_year_start': getattr(settings, 'FINANCIAL_YEAR_START', 'JANUARY'),
        'fiscal_year_end': getattr(settings, 'FINANCIAL_YEAR_END', 'DECEMBER'),
        'installed_apps': len(settings.INSTALLED_APPS),
        'debug_mode': settings.DEBUG,
        'timezone': str(settings.TIME_ZONE),
    }
    
    return Response(system_info)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Get dashboard summary data."""
    from chart_of_accounts.models import ChartOfAccount
    from journal_entries.models import JournalEntry
    from financial_statements.models import FinancialStatement
    
    try:
        # Get account counts
        total_accounts = ChartOfAccount.objects.filter(is_active=True).count()
        active_accounts = ChartOfAccount.objects.filter(status='active', is_active=True).count()
        
        # Get journal entry counts
        total_entries = JournalEntry.objects.count()
        posted_entries = JournalEntry.objects.filter(status='posted').count()
        pending_entries = JournalEntry.objects.filter(status='pending').count()
        
        # Get financial statement counts
        total_statements = FinancialStatement.objects.count()
        published_statements = FinancialStatement.objects.filter(status='published').count()
        
        # Get recent activity
        recent_entries = JournalEntry.objects.order_by('-created_at')[:5]
        recent_statements = FinancialStatement.objects.order_by('-created_at')[:5]
        
        dashboard_data = {
            'accounts': {
                'total': total_accounts,
                'active': active_accounts,
            },
            'journal_entries': {
                'total': total_entries,
                'posted': posted_entries,
                'pending': pending_entries,
            },
            'financial_statements': {
                'total': total_statements,
                'published': published_statements,
            },
            'recent_activity': {
                'journal_entries': [
                    {
                        'entry_number': entry.entry_number,
                        'description': entry.description[:50],
                        'status': entry.status,
                        'created_at': entry.created_at.isoformat(),
                    }
                    for entry in recent_entries
                ],
                'financial_statements': [
                    {
                        'statement_code': stmt.statement_code,
                        'statement_name': stmt.statement_name,
                        'status': stmt.status,
                        'created_at': stmt.created_at.isoformat(),
                    }
                    for stmt in recent_statements
                ]
            }
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        return Response({
            'error': 'Failed to load dashboard data',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """Export data in various formats."""
    export_type = request.data.get('type', 'excel')
    data_type = request.data.get('data_type', 'chart_of_accounts')
    filters = request.data.get('filters', {})
    
    # TODO: Implement data export logic
    # This would include Excel, PDF, CSV export functionality
    
    return Response({
        'message': f'Export of {data_type} in {export_type} format initiated',
        'export_id': 'EXP001',  # Placeholder
        'status': 'processing'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_data(request):
    """Import data from external sources."""
    import_type = request.data.get('type', 'chart_of_accounts')
    source_system = request.data.get('source_system', 'manual')
    file_data = request.FILES.get('file')
    
    if not file_data:
        return Response({
            'error': 'No file provided for import'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # TODO: Implement data import logic
    # This would include validation, mapping, and import functionality
    
    return Response({
        'message': f'Import of {import_type} from {source_system} initiated',
        'import_id': 'IMP001',  # Placeholder
        'status': 'processing',
        'records_processed': 0
    })
