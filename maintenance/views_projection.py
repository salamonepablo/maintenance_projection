"""
Vistas para proyección de mantenimiento.
"""
from __future__ import annotations

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
        module_number__in=[47, 67]
    ).order_by('module_number')
    
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
        module_number__in=[47, 67]
    ).order_by('module_number')
    
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
        module_number__in=[47, 67]
    ).order_by('module_number')
    
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
