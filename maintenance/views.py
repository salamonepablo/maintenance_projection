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
        # ✅ FIX: Usar daily_delta_km en lugar de restar lecturas
        # Esto es más preciso y respeta los deltas ya calculados
        month_deltas = OdometerLog.objects.filter(
            fleet_module=module,
            reading_date__gte=first_day_of_month
        ).values_list('daily_delta_km', flat=True)
        
        # Sumar todos los deltas del mes (ignora None)
        km_this_month = sum(km for km in month_deltas if km is not None and km > 0)
        
        # Último evento de mantenimiento
        last_event = MaintenanceEvent.objects.filter(
            fleet_module=module
        ).order_by('-event_date', '-id').first()
        
        if last_event:
            days_since_event = (today - last_event.event_date).days
            
            # ✅ FIX: Calcular km desde evento usando current_km - km_at_event
            current_km = module.total_accumulated_km
            km_since_event = current_km - last_event.odometer_km
            
            # Validación: no puede ser negativo
            if km_since_event < 0:
                km_since_event = 0
                
            last_event_data = {
                'type': last_event.profile.code,
                'date': last_event.event_date,
                'days_ago': days_since_event,
                'km_since': km_since_event,
                'km_at_event': last_event.odometer_km,
            }
        else:
            last_event_data = None
        
        # ✅ FIX: Promedio diario usando daily_delta_km
        thirty_days_ago = today - timedelta(days=30)
        recent_deltas = OdometerLog.objects.filter(
            fleet_module=module,
            reading_date__gte=thirty_days_ago
        ).values_list('daily_delta_km', 'reading_date')
        
        # Filtrar solo deltas positivos y calcular promedio
        valid_deltas = [km for km, _ in recent_deltas if km is not None and km > 0]
        
        if valid_deltas:
            daily_avg = sum(valid_deltas) / len(valid_deltas)
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
