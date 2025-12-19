"""
Vistas para Dashboard y proyección de mantenimiento.
"""
from maintenance.views_projection import (
    projection_api,
    projection_export_excel,
    projection_view,
)

import os
import tempfile
from datetime import date

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, FileResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from maintenance.models import FleetModule
from maintenance.services.projection_grid import MaintenanceProjectionGrid
from maintenance.services.projection_excel import ProjectionExcelExporter

@require_http_methods(["GET"])
def projection_view(request: HttpRequest) -> HttpResponse:
    """
    Vista principal de proyección de mantenimiento.
    Muestra grilla HTML con proyección mes a mes.
    """
    # Obtener parámetros de query string
    try:
        months_ahead = int(request.GET.get('months', 24))
        monthly_km = int(request.GET.get('monthly_km', 12_500))
    except ValueError:
        months_ahead = 24
        monthly_km = 12_500
    
    # Validaciones
    if months_ahead < 1 or months_ahead > 60:
        months_ahead = 24
    if monthly_km < 1000 or monthly_km > 50_000:
        monthly_km = 12_500
    
    # Obtener módulos activos (excluir 47 y 67 que están fuera de servicio)
    modules = FleetModule.objects.exclude(
        id__in=[47, 67]
    ).order_by('id')
    
    # Generar proyecciones
    grid_service = MaintenanceProjectionGrid(monthly_km=monthly_km)
    
    try:
        projections = grid_service.generate_for_all_modules(
            modules=list(modules),
            months_ahead=months_ahead,
            start_date=date.today()
        )
        
        # Convertir a formato para template
        projection_data = grid_service.export_to_dict(projections)
        
        context = {
            'projections': projection_data,
            'months_ahead': months_ahead,
            'monthly_km': monthly_km,
            'total_modules': len(modules),
            'generation_date': date.today(),
        }
        
        return render(request, 'maintenance/projection.html', context)
    
    except Exception as e:
        messages.error(
            request,
            f'Error al generar proyección: {str(e)}'
        )
        
        context = {
            'projections': None,
            'months_ahead': months_ahead,
            'monthly_km': monthly_km,
            'total_modules': 0,
            'generation_date': date.today(),
        }
        
        return render(request, 'maintenance/projection.html', context)


@require_http_methods(["GET"])
def projection_export_excel(request: HttpRequest) -> HttpResponse:
    """
    Exporta proyección a Excel.
    """
    # Obtener parámetros
    try:
        months_ahead = int(request.GET.get('months', 24))
        monthly_km = int(request.GET.get('monthly_km', 12_500))
    except ValueError:
        months_ahead = 24
        monthly_km = 12_500
    
    # Validaciones
    if months_ahead < 1 or months_ahead > 60:
        months_ahead = 24
    if monthly_km < 1000 or monthly_km > 50_000:
        monthly_km = 12_500
    
    # Obtener módulos activos
    modules = FleetModule.objects.exclude(
        id__in=[47, 67]
    ).order_by('id')
    
    # Generar proyecciones
    grid_service = MaintenanceProjectionGrid(monthly_km=monthly_km)
    
    try:
        projections = grid_service.generate_for_all_modules(
            modules=list(modules),
            months_ahead=months_ahead,
            start_date=date.today()
        )
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.xlsx',
            delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name
        
        # Exportar a Excel
        exporter = ProjectionExcelExporter()
        exporter.export(
            projections=projections,
            filepath=tmp_path,
            monthly_km=monthly_km
        )
        
        # Leer archivo y enviarlo
        with open(tmp_path, 'rb') as f:
            response = HttpResponse(
                f.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            filename = f'proyeccion_mantenimiento_{date.today().strftime("%Y%m%d")}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        
        return response
    
    except Exception as e:
        messages.error(
            request,
            f'Error al exportar a Excel: {str(e)}'
        )
        # Redirigir a vista principal
        return HttpResponse(
            f'Error al exportar: {str(e)}',
            status=500
        )


@require_http_methods(["GET"])
def projection_api(request: HttpRequest) -> HttpResponse:
    """
    API JSON para obtener proyecciones.
    Útil para consumir desde frontend/React.
    """
    import json
    
    # Obtener parámetros
    try:
        months_ahead = int(request.GET.get('months', 24))
        monthly_km = int(request.GET.get('monthly_km', 12_500))
    except ValueError:
        return HttpResponse(
            json.dumps({'error': 'Parámetros inválidos'}),
            content_type='application/json',
            status=400
        )
    
    # Validaciones
    if months_ahead < 1 or months_ahead > 60:
        return HttpResponse(
            json.dumps({'error': 'months debe estar entre 1 y 60'}),
            content_type='application/json',
            status=400
        )
    if monthly_km < 1000 or monthly_km > 50_000:
        return HttpResponse(
            json.dumps({'error': 'monthly_km debe estar entre 1000 y 50000'}),
            content_type='application/json',
            status=400
        )
    
    # Obtener módulos activos
    modules = FleetModule.objects.exclude(
        id__in=[47, 67]
    ).order_by('id')
    
    # Generar proyecciones
    grid_service = MaintenanceProjectionGrid(monthly_km=monthly_km)
    
    try:
        projections = grid_service.generate_for_all_modules(
            modules=list(modules),
            months_ahead=months_ahead,
            start_date=date.today()
        )
        
        # Convertir a dict
        result = grid_service.export_to_dict(projections)
        result['generation_date'] = date.today().isoformat()
        result['params'] = {
            'months_ahead': months_ahead,
            'monthly_km': monthly_km,
        }
        
        return HttpResponse(
            json.dumps(result, indent=2),
            content_type='application/json'
        )
    
    except Exception as e:
        return HttpResponse(
            json.dumps({'error': str(e)}),
            content_type='application/json',
            status=500
        )
"""
Vistas para proyección de mantenimiento.
"""
#from __future__ import annotations

#import os
#import tempfile
#from datetime import date

#from django.contrib import messages
#from django.http import HttpRequest, HttpResponse, FileResponse
#from django.shortcuts import render
#from django.views.decorators.http import require_http_methods

#from maintenance.models import FleetModule
#from maintenance.services.projection_grid import MaintenanceProjectionGrid
#from maintenance.services.projection_excel import ProjectionExcelExporter


@require_http_methods(["GET"])
def projection_view(request: HttpRequest) -> HttpResponse:
    """
    Vista principal de proyección de mantenimiento.
    Muestra grilla HTML con proyección mes a mes.
    """
    # Obtener parámetros de query string
    try:
        months_ahead = int(request.GET.get('months', 24))
        monthly_km = int(request.GET.get('monthly_km', 12_500))
    except ValueError:
        months_ahead = 24
        monthly_km = 12_500
    
    # Validaciones
    if months_ahead < 1 or months_ahead > 60:
        months_ahead = 24
    if monthly_km < 1000 or monthly_km > 50_000:
        monthly_km = 12_500
    
    # Obtener módulos activos (excluir 47 y 67 que están fuera de servicio)
    modules = FleetModule.objects.exclude(
        id__in=[47, 67]
    ).order_by('id')
    
    # Generar proyecciones
    grid_service = MaintenanceProjectionGrid(monthly_km=monthly_km)
    
    try:
        projections = grid_service.generate_for_all_modules(
            modules=list(modules),
            months_ahead=months_ahead,
            start_date=date.today()
        )
        
        # Convertir a formato para template
        projection_data = grid_service.export_to_dict(projections)
        
        context = {
            'projections': projection_data,
            'months_ahead': months_ahead,
            'monthly_km': monthly_km,
            'total_modules': len(modules),
            'generation_date': date.today(),
        }
        
        return render(request, 'maintenance/projection.html', context)
    
    except Exception as e:
        messages.error(
            request,
            f'Error al generar proyección: {str(e)}'
        )
        
        context = {
            'projections': None,
            'months_ahead': months_ahead,
            'monthly_km': monthly_km,
            'total_modules': 0,
            'generation_date': date.today(),
        }
        
        return render(request, 'maintenance/projection.html', context)


@require_http_methods(["GET"])
def projection_export_excel(request: HttpRequest) -> HttpResponse:
    """
    Exporta proyección a Excel.
    """
    # Obtener parámetros
    try:
        months_ahead = int(request.GET.get('months', 24))
        monthly_km = int(request.GET.get('monthly_km', 12_500))
    except ValueError:
        months_ahead = 24
        monthly_km = 12_500
    
    # Validaciones
    if months_ahead < 1 or months_ahead > 60:
        months_ahead = 24
    if monthly_km < 1000 or monthly_km > 50_000:
        monthly_km = 12_500
    
    # Obtener módulos activos
    modules = FleetModule.objects.exclude(
        id__in=[47, 67]
    ).order_by('id')
    
    # Generar proyecciones
    grid_service = MaintenanceProjectionGrid(monthly_km=monthly_km)
    
    try:
        projections = grid_service.generate_for_all_modules(
            modules=list(modules),
            months_ahead=months_ahead,
            start_date=date.today()
        )
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.xlsx',
            delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name
        
        # Exportar a Excel
        exporter = ProjectionExcelExporter()
        exporter.export(
            projections=projections,
            filepath=tmp_path,
            monthly_km=monthly_km
        )
        
        # Leer archivo y enviarlo
        with open(tmp_path, 'rb') as f:
            response = HttpResponse(
                f.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            filename = f'proyeccion_mantenimiento_{date.today().strftime("%Y%m%d")}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        
        return response
    
    except Exception as e:
        messages.error(
            request,
            f'Error al exportar a Excel: {str(e)}'
        )
        # Redirigir a vista principal
        return HttpResponse(
            f'Error al exportar: {str(e)}',
            status=500
        )


@require_http_methods(["GET"])
def projection_api(request: HttpRequest) -> HttpResponse:
    """
    API JSON para obtener proyecciones.
    Útil para consumir desde frontend/React.
    """
    import json
    
    # Obtener parámetros
    try:
        months_ahead = int(request.GET.get('months', 24))
        monthly_km = int(request.GET.get('monthly_km', 12_500))
    except ValueError:
        return HttpResponse(
            json.dumps({'error': 'Parámetros inválidos'}),
            content_type='application/json',
            status=400
        )
    
    # Validaciones
    if months_ahead < 1 or months_ahead > 60:
        return HttpResponse(
            json.dumps({'error': 'months debe estar entre 1 y 60'}),
            content_type='application/json',
            status=400
        )
    if monthly_km < 1000 or monthly_km > 50_000:
        return HttpResponse(
            json.dumps({'error': 'monthly_km debe estar entre 1000 y 50000'}),
            content_type='application/json',
            status=400
        )
    
    # Obtener módulos activos
    modules = FleetModule.objects.exclude(
        id__in=[47, 67]
    ).order_by('id')
    
    # Generar proyecciones
    grid_service = MaintenanceProjectionGrid(monthly_km=monthly_km)
    
    try:
        projections = grid_service.generate_for_all_modules(
            modules=list(modules),
            months_ahead=months_ahead,
            start_date=date.today()
        )
        
        # Convertir a dict
        result = grid_service.export_to_dict(projections)
        result['generation_date'] = date.today().isoformat()
        result['params'] = {
            'months_ahead': months_ahead,
            'monthly_km': monthly_km,
        }
        
        return HttpResponse(
            json.dumps(result, indent=2),
            content_type='application/json'
        )
    
    except Exception as e:
        return HttpResponse(
            json.dumps({'error': str(e)}),
            content_type='application/json',
            status=500
        )
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
        ).order_by('-maintenance_date', '-id').first()
        
        if last_event:
            days_since_event = (today - last_event.maintenance_date).days
            
            # Calcular km desde el evento
            events_after = OdometerLog.objects.filter(
                fleet_module=module,
                reading_date__gte=last_event.maintenance_date
            ).order_by('reading_date')
            
            first_after = events_after.first()
            last_after = events_after.last()
            
            if first_after and last_after:
                km_since_event = last_after.odometer_reading - last_event.odometer_km
            else:
                km_since_event = module.total_accumulated_km - last_event.odometer_km
                
            last_event_data = {
                'type': last_event.maintenance_profile.cycle_type,
                'date': last_event.maintenance_date,
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