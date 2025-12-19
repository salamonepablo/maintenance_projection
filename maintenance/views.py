"""
Vistas para Dashboard y proyección de mantenimiento.
"""
from maintenance.views_projection import (
    projection_api,
    projection_export_excel,
    projection_view,
)

from datetime import date, timedelta

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from maintenance.models import FleetModule, OdometerLog, MaintenanceEvent


# Las vistas de proyección se importan desde maintenance.views_projection
@require_http_methods(["GET"])
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """
    Vista principal del dashboard de flota.
    Muestra resumen de todos los módulos o detalle de un módulo específico.
    """
    # Obtener parámetro de filtro
    module_filter = request.GET.get('module', '')
    
    # Fecha actual y primer día del mes
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)
    
    # Query base de módulos (excluir fuera de servicio)
    modules_query = FleetModule.objects.exclude(id__in=[47, 67]).order_by('id')
    
    # Si hay filtro, aplicarlo
    if module_filter:
        try:
            module_id = int(module_filter)
            modules_query = modules_query.filter(id=module_id)
        except ValueError:
            pass
    
    # Construir datos de cada módulo
    modules_data = []
    
    for module in modules_query:
        # Km del mes actual
        month_logs = OdometerLog.objects.filter(
            fleet_module=module,
            reading_date__gte=first_day_of_month
        ).order_by('reading_date')
        
        first_reading = month_logs.first()
        last_reading = month_logs.last()
        
        if first_reading and last_reading:
            km_this_month = last_reading.odometer_reading - first_reading.odometer_reading
        else:
            km_this_month = 0
        
        # Último evento de mantenimiento
        last_event = MaintenanceEvent.objects.filter(
            fleet_module=module
        ).order_by('-event_date', '-id').first()
        
        if last_event:
            days_since_event = (today - last_event.event_date).days
            
            # Calcular km desde el evento
            events_after = OdometerLog.objects.filter(
                fleet_module=module,
                reading_date__gte=last_event.event_date
            ).order_by('reading_date')
            
            first_after = events_after.first()
            last_after = events_after.last()
            
            if first_after and last_after:
                km_since_event = last_after.odometer_reading - last_event.odometer_km
            else:
                km_since_event = module.total_accumulated_km - last_event.odometer_km
                
            last_event_data = {
                'type': last_event.profile.code,
                'date': last_event.event_date,
                'days_ago': days_since_event,
                'km_since': km_since_event,
                'km_at_event': last_event.odometer_km,
            }
        else:
            last_event_data = None
        
        # Promedio diario últimos 30 días
        thirty_days_ago = today - timedelta(days=30)
        recent_logs = OdometerLog.objects.filter(
            fleet_module=module,
            reading_date__gte=thirty_days_ago
        ).order_by('reading_date')
        
        first_recent = recent_logs.first()
        last_recent = recent_logs.last()
        
        if first_recent and last_recent and first_recent != last_recent:
            days_diff = (last_recent.reading_date - first_recent.reading_date).days
            if days_diff > 0:
                km_diff = last_recent.odometer_reading - first_recent.odometer_reading
                daily_avg = km_diff / days_diff
            else:
                daily_avg = 0
        else:
            daily_avg = 0
        
        modules_data.append({
            'module': module,
            'km_this_month': int(km_this_month),
            'last_event': last_event_data,
            'daily_avg_km': int(daily_avg),
        })
    
    # Estadísticas generales
    if not module_filter:
        total_modules = len(modules_data)
        total_km_month = sum(m['km_this_month'] for m in modules_data)
        avg_daily_fleet = sum(m['daily_avg_km'] for m in modules_data) / total_modules if total_modules > 0 else 0
        
        stats = {
            'total_modules': total_modules,
            'total_km_month': total_km_month,
            'avg_daily_fleet': int(avg_daily_fleet),
        }
    else:
        stats = None
    
    context = {
        'modules_data': modules_data,
        'stats': stats,
        'month_name': today.strftime('%B %Y'),
        'filtered_module': module_filter,
        'all_modules': FleetModule.objects.exclude(id__in=[47, 67]).order_by('id'),
    }
    
    return render(request, 'maintenance/dashboard.html', context)