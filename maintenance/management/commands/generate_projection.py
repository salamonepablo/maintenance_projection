"""
Comando de management para generar proyecciones de mantenimiento.

Uso:
    python manage.py generate_projection --months 24 --km 12500 --output projection.xlsx
    python manage.py generate_projection --module 5 --json
    python manage.py generate_projection --all --excel
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import date
import json

from maintenance.models import FleetModule
from maintenance.services.projection_grid import MaintenanceProjectionGrid
from maintenance.services.projection_excel import ProjectionExcelExporter


class Command(BaseCommand):
    help = 'Genera proyección de mantenimiento para módulos'

    def add_arguments(self, parser):
        # Opciones de alcance
        parser.add_argument(
            '--module',
            type=int,
            help='Número de módulo específico (ej: 5)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generar para todos los módulos activos'
        )
        
        # Parámetros de proyección
        parser.add_argument(
            '--months',
            type=int,
            default=24,
            help='Cantidad de meses a proyectar (default: 24)'
        )
        parser.add_argument(
            '--km',
            type=int,
            default=12_500,
            help='Km promedio mensual (default: 12500)'
        )
        
        # Formato de salida
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output en formato JSON a stdout'
        )
        parser.add_argument(
            '--excel',
            action='store_true',
            help='Generar archivo Excel'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Ruta del archivo de salida (para --excel)'
        )
        
        # Opciones adicionales
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada'
        )

    def handle(self, *args, **options):
        # Validar parámetros
        months = options['months']
        monthly_km = options['km']
        
        if months < 1 or months > 60:
            raise CommandError('months debe estar entre 1 y 60')
        
        if monthly_km < 1000 or monthly_km > 50_000:
            raise CommandError('km debe estar entre 1000 y 50000')
        
        # Determinar módulos a procesar
        if options['module']:
            try:
                modules = [FleetModule.objects.get(id=options['module'])]
                if options['verbose']:
                    self.stdout.write(f"Procesando módulo {options['module']}")
            except FleetModule.DoesNotExist:
                raise CommandError(f"Módulo {options['module']} no existe")
        
        elif options['all']:
            modules = list(
                FleetModule.objects.exclude(id__in=[47, 67])
                .order_by('id')
            )
            if options['verbose']:
                self.stdout.write(f"Procesando {len(modules)} módulos")
        
        else:
            raise CommandError(
                'Debe especificar --module <num> o --all'
            )
        
        # Generar proyecciones
        service = MaintenanceProjectionGrid(monthly_km=monthly_km)
        
        if options['verbose']:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Generando proyección: {months} meses, {monthly_km} km/mes"
                )
            )
        
        try:
            if len(modules) == 1:
                # Proyección para un solo módulo
                rows = service.generate_for_module(
                    modules[0],
                    months_ahead=months
                )
                projections = {modules[0].id: rows}
            else:
                # Proyección para múltiples módulos
                projections = service.generate_for_all_modules(
                    modules,
                    months_ahead=months
                )
            
            # Output según formato solicitado
            if options['json']:
                self._output_json(service, projections)
            
            elif options['excel']:
                self._output_excel(
                    projections,
                    monthly_km,
                    options.get('output')
                )
            
            else:
                # Output de texto por defecto
                self._output_text(projections, months, monthly_km)
            
            if options['verbose']:
                self.stdout.write(
                    self.style.SUCCESS('✓ Proyección generada exitosamente')
                )
        
        except Exception as e:
            raise CommandError(f'Error al generar proyección: {str(e)}')
    
    def _output_text(self, projections, months, monthly_km):
        """Output de texto simple a stdout"""
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== PROYECCIÓN DE MANTENIMIENTO ===\n'
            )
        )
        self.stdout.write(f'Fecha: {date.today().strftime("%d/%m/%Y")}')
        self.stdout.write(f'Meses: {months}')
        self.stdout.write(f'Km/mes: {monthly_km:,}\n')
        
        for module_num in sorted(projections.keys()):
            rows = projections[module_num]
            
            self.stdout.write(
                self.style.WARNING(f'\n--- Módulo {module_num} ---')
            )
            
            for row in rows:
                self.stdout.write(
                    f'  {row.intervention_type}: '
                    f'Km inicial {row.initial_km:,}, '
                    f'Última fecha: {row.last_event_date or "N/A"}'
                )
                
                # Mostrar proyección de primeros 3 meses
                for cell in row.cells[:3]:
                    status = ''
                    if cell.is_reset_point:
                        status = ' [RESETEO]'
                    elif cell.exceeds_threshold:
                        status = ' [EXCEDE UMBRAL]'
                    
                    self.stdout.write(
                        f'    {cell.month_date.strftime("%b %y")}: '
                        f'{cell.km_accumulated:,} km{status}'
                    )
                
                if len(row.cells) > 3:
                    self.stdout.write(f'    ... (+{len(row.cells) - 3} meses)')
    
    def _output_json(self, service, projections):
        """Output JSON a stdout"""
        data = service.export_to_dict(projections)
        data['generation_date'] = date.today().isoformat()
        
        self.stdout.write(
            json.dumps(data, indent=2, ensure_ascii=False)
        )
    
    def _output_excel(self, projections, monthly_km, output_path):
        """Generar archivo Excel"""
        if not output_path:
            output_path = f'proyeccion_{date.today().strftime("%Y%m%d")}.xlsx'
        
        exporter = ProjectionExcelExporter()
        exporter.export(
            projections=projections,
            filepath=output_path,
            monthly_km=monthly_km
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Excel generado: {output_path}')
        )
        
        # Intentar recalcular fórmulas si está disponible
        try:
            import subprocess
            result = subprocess.run(
                ['python', 'recalc.py', output_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS('✓ Fórmulas recalculadas')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠ No se pudo recalcular fórmulas (opcional)'
                    )
                )
        except Exception:
            pass  # Recalc es opcional
