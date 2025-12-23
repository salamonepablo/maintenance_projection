"""
Comando Django para sincronizar datos desde Access.

Uso:
    python manage.py sync_from_access [opciones]

Opciones:
    --test              Solo muestra qué haría sin modificar BD
    --full              Sincroniza todo desde cero
    --modules-only      Solo sincroniza módulos
    --events-only       Solo sincroniza eventos de mantenimiento
    --readings-only     Solo sincroniza lecturas de odómetro
    --since YYYY-MM-DD  Solo sincroniza datos desde esta fecha
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from datetime import datetime, date, timedelta
from typing import Optional

from maintenance.models import (
    FleetModule,
    MaintenanceEvent,
    OdometerLog,
    MaintenanceProfile
)
from maintenance.services.access_extractor import (
    AccessExtractor,
    ModuleData,
    MaintenanceEventData,
    OdometerReadingData
)


class Command(BaseCommand):
    help = 'Sincroniza datos desde Access (DB_CCEE_Mantenimiento)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Modo prueba: muestra qué haría sin modificar BD',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Sincronización completa desde cero',
        )
        parser.add_argument(
            '--modules-only',
            action='store_true',
            help='Solo sincronizar módulos',
        )
        parser.add_argument(
            '--events-only',
            action='store_true',
            help='Solo sincronizar eventos de mantenimiento',
        )
        parser.add_argument(
            '--readings-only',
            action='store_true',
            help='Solo sincronizar lecturas de odómetro',
        )
        parser.add_argument(
            '--since',
            type=str,
            help='Sincronizar solo desde fecha (YYYY-MM-DD)',
        )
    
    def handle(self, *args, **options):
        """Ejecuta la sincronización."""
        
        # Validar configuración
        connection_string = getattr(settings, 'ACCESS_CONNECTION_STRING', None)
        if not connection_string:
            raise CommandError(
                'Falta ACCESS_CONNECTION_STRING en settings. '
                'Ver INSTALACION.md para configuración.'
            )
        
        # Modo de operación
        is_test = options['test']
        is_full = options['full']
        since_date = self._parse_date(options.get('since'))
        
        # Determinar qué sincronizar
        sync_modules = options['modules_only'] or is_full or (
            not options['events_only'] and not options['readings_only']
        )
        sync_events = options['events_only'] or is_full or (
            not options['modules_only'] and not options['readings_only']
        )
        sync_readings = options['readings_only'] or is_full or (
            not options['modules_only'] and not options['events_only']
        )
        
        if is_test:
            self.stdout.write(self.style.WARNING('MODO PRUEBA - No se modificará la BD'))
        
        self.stdout.write('Conectando a Access...')
        
        try:
            with AccessExtractor(connection_string) as extractor:
                # Test de conexión
                stats = extractor.test_connection()
                if not stats.get('connected'):
                    raise CommandError(f"Error de conexión: {stats.get('error')}")
                
                self.stdout.write(self.style.SUCCESS('✓ Conexión exitosa'))
                self.stdout.write(
                    f"  Módulos CSR en Access: {stats.get('modules_count', 0)}"
                )
                self.stdout.write(
                    f"  Eventos en Access: {stats.get('events_count', 0)}"
                )
                self.stdout.write(
                    f"  Lecturas en Access: {stats.get('readings_count', 0)}"
                )
                self.stdout.write('')
                
                # Sincronizar módulos
                if sync_modules:
                    modules_synced = self._sync_modules(extractor, is_test)
                    self.stdout.write('')
                
                # Sincronizar eventos
                if sync_events:
                    events_synced = self._sync_events(
                        extractor, is_test, since_date
                    )
                    self.stdout.write('')
                
                # Sincronizar lecturas
                if sync_readings:
                    readings_synced = self._sync_readings(
                        extractor, is_test, since_date
                    )
                    self.stdout.write('')
                
                # Resumen final
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(self.style.SUCCESS('SINCRONIZACIÓN COMPLETADA'))
                self.stdout.write(self.style.SUCCESS('='*60))
                
                if sync_modules:
                    self.stdout.write(f"Módulos sincronizados: {modules_synced}")
                if sync_events:
                    self.stdout.write(f"Eventos sincronizados: {events_synced}")
                if sync_readings:
                    self.stdout.write(f"Lecturas sincronizadas: {readings_synced}")
        
        except Exception as e:
            raise CommandError(f"Error durante sincronización: {e}")
    
    def _sync_modules(
        self,
        extractor: AccessExtractor,
        is_test: bool
    ) -> int:
        """Sincroniza módulos desde Access."""
        
        self.stdout.write('Sincronizando módulos...')
        
        modules_data = extractor.get_active_modules()
        synced_count = 0
        
        if is_test:
            self.stdout.write(f"  Se sincronizarían {len(modules_data)} módulos:")
            for mod in modules_data[:10]:
                self.stdout.write(
                    f"    {mod.module_id} (#{mod.module_number}) "
                    f"→ Formación: {mod.formation or 'N/A'}"
                )
            if len(modules_data) > 10:
                self.stdout.write(f"    ... y {len(modules_data) - 10} más")
            return len(modules_data)
        
        # Sincronización real
        with transaction.atomic():
            for mod_data in modules_data:
                module, created = FleetModule.objects.update_or_create(
                    module_number=mod_data.module_number,
                    defaults={
                        'module_type': self._determine_module_type(
                            mod_data.module_number
                        ),
                        'is_active': True,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Creado: {mod_data.module_id}")
                    )
                
                synced_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"✓ {synced_count} módulos sincronizados"))
        return synced_count
    
    def _sync_events(
        self,
        extractor: AccessExtractor,
        is_test: bool,
        since_date: Optional[date]
    ) -> int:
        """Sincroniza eventos de mantenimiento desde Access."""
        
        self.stdout.write('Sincronizando eventos de mantenimiento...')
        
        # Determinar desde qué fecha sincronizar
        if since_date:
            self.stdout.write(f"  Desde: {since_date.strftime('%d/%m/%Y')}")
        elif not is_test:
            # Si no es full sync, solo últimos 30 días
            since_date = date.today() - timedelta(days=30)
            self.stdout.write(f"  Últimos 30 días (desde {since_date.strftime('%d/%m/%Y')})")
        
        events_data = extractor.get_maintenance_events(since_date=since_date)
        synced_count = 0
        
        if is_test:
            self.stdout.write(f"  Se sincronizarían {len(events_data)} eventos:")
            for evt in events_data[:10]:
                self.stdout.write(
                    f"    {evt.module_id} - {evt.maintenance_type} "
                    f"({evt.event_date.strftime('%d/%m/%Y')}) "
                    f"@ {evt.odometer_km:,} km"
                )
            if len(events_data) > 10:
                self.stdout.write(f"    ... y {len(events_data) - 10} más")
            return len(events_data)
        
        # Sincronización real
        skipped_count = 0
        
        with transaction.atomic():
            for evt_data in events_data:
                # Buscar módulo
                module_num = AccessExtractor.extract_module_number(evt_data.module_id)
                if not module_num:
                    skipped_count += 1
                    continue
                
                try:
                    module = FleetModule.objects.get(module_number=module_num)
                except FleetModule.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Módulo {evt_data.module_id} no existe en BD"
                        )
                    )
                    skipped_count += 1
                    continue
                
                # Buscar perfil de mantenimiento
                try:
                    profile = MaintenanceProfile.objects.get(
                        cycle_type=evt_data.maintenance_type
                    )
                except MaintenanceProfile.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Perfil {evt_data.maintenance_type} no existe"
                        )
                    )
                    skipped_count += 1
                    continue
                
                # Crear o actualizar evento
                event, created = MaintenanceEvent.objects.get_or_create(
                    module=module,
                    profile=profile,
                    event_date=evt_data.event_date,
                    defaults={
                        'odometer_km': evt_data.odometer_km,
                    }
                )
                
                if not created and event.odometer_km != evt_data.odometer_km:
                    event.odometer_km = evt_data.odometer_km
                    event.save()
                
                synced_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ {synced_count} eventos sincronizados")
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"  ⚠ {skipped_count} eventos omitidos")
            )
        
        return synced_count
    
    def _sync_readings(
        self,
        extractor: AccessExtractor,
        is_test: bool,
        since_date: Optional[date]
    ) -> int:
        """Sincroniza lecturas de odómetro desde Access."""
        
        self.stdout.write('Sincronizando lecturas de odómetro...')
        
        # Determinar desde qué fecha sincronizar
        if since_date:
            self.stdout.write(f"  Desde: {since_date.strftime('%d/%m/%Y')}")
        elif not is_test:
            # Si no es full sync, solo últimos 7 días
            since_date = date.today() - timedelta(days=7)
            self.stdout.write(f"  Últimos 7 días (desde {since_date.strftime('%d/%m/%Y')})")
        
        readings_data = extractor.get_odometer_readings(since_date=since_date)
        synced_count = 0
        
        if is_test:
            self.stdout.write(f"  Se sincronizarían {len(readings_data)} lecturas:")
            for reading in readings_data[:10]:
                self.stdout.write(
                    f"    {reading.module_id} - {reading.odometer_reading:,} km "
                    f"({reading.reading_date.strftime('%d/%m/%Y')})"
                )
            if len(readings_data) > 10:
                self.stdout.write(f"    ... y {len(readings_data) - 10} más")
            return len(readings_data)
        
        # Sincronización real
        skipped_count = 0
        
        with transaction.atomic():
            for reading_data in readings_data:
                # Buscar módulo
                module_num = AccessExtractor.extract_module_number(reading_data.module_id)
                if not module_num:
                    skipped_count += 1
                    continue
                
                try:
                    module = FleetModule.objects.get(module_number=module_num)
                except FleetModule.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Módulo {reading_data.module_id} no existe en BD"
                        )
                    )
                    skipped_count += 1
                    continue
                
                # Crear lectura (solo si no existe ya)
                _, created = OdometerLog.objects.get_or_create(
                    module=module,
                    reading_date=reading_data.reading_date,
                    defaults={
                        'odometer_reading': reading_data.odometer_reading,
                    }
                )
                
                if created:
                    synced_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ {synced_count} lecturas sincronizadas")
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"  ⚠ {skipped_count} lecturas omitidas")
            )
        
        return synced_count
    
    @staticmethod
    def _determine_module_type(module_number: int) -> str:
        """
        Determina el tipo de módulo según su número.
        
        Módulos CSR:
        - 1-42: Cuádrupla
        - 43-86: Tripla
        
        Args:
            module_number: Número del módulo (1-86)
        
        Returns:
            'CUADRUPLA' o 'TRIPLA'
        """
        if module_number <= 42:
            return 'CUADRUPLA'
        else:
            return 'TRIPLA'
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[date]:
        """Parsea una fecha en formato YYYY-MM-DD."""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError(
                f"Formato de fecha inválido: {date_str}. "
                "Use YYYY-MM-DD (ej: 2025-01-15)"
            )
