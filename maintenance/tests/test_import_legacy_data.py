"""
Tests unitarios para el comando import_legacy_data.

Valida la correcta importación de módulos, eventos y lecturas desde CSVs.
"""
from __future__ import annotations

import tempfile
from datetime import date
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from maintenance.models import FleetModule, MaintenanceEvent, MaintenanceProfile, OdometerLog


class ImportLegacyDataCommandTests(TestCase):
    """Tests para el comando de importación de datos legacy."""

    def setUp(self):
        """Configura archivos CSV de prueba en memoria."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # CSV de módulos
        self.modulos_csv = self.temp_path / "test_modulos.csv"
        self.modulos_csv.write_text(
            "FORMACION;MODULO;MC1;R1;R2;MC2\n"
            "120;01;5001;5601;5801;5002\n"
            "120;20;5039;5620;5820;5040\n"
            "121;45;5089;5645;;5090\n"  # Tripla (id >= 43)
        )

        # CSV de eventos (formato SIMAF)
        self.eventos_csv = self.temp_path / "test_eventos.csv"
        self.eventos_csv.write_text(
            "Id_OT_Simaf;Formaciones;Módulos;OT_Simaf;Ingreso;Tipo_Tarea;Tarea;Km;Fecha_Inicio;Fecha_Fin;Observaciones;Clase_Vehículos\n"
            "1;120;1;1001;Programado;Preventivo;IQ1;1.000.000,00;01/01/2025;02/01/2025;Inspección quincenal;C\n"
            "2;120;1;1002;Programado;Preventivo;AN1;1.200.000,00;15/06/2025;20/06/2025;Revisión anual;C\n"
            "3;120;20;1003;Programado;Preventivo;IB;950.000,00;10/03/2025;11/03/2025;Bimestral;C\n",
            encoding="utf-8"
        )

        # CSV de lecturas
        self.lecturas_csv = self.temp_path / "test_lecturas.csv"
        self.lecturas_csv.write_text(
            "Id_Kilometrajes;Módulo;kilometraje;Fecha\n"
            "1;M01;1.000.000,00;01/01/2025\n"
            "2;M01;1.050.000,00;15/01/2025\n"
            "3;M01;1.100.000,00;01/02/2025\n"
            "4;M20;950.000,00;10/03/2025\n"
            "5;M20;975.000,00;25/03/2025\n"
        )

    def test_import_modules_creates_fleet_modules(self):
        """Valida que se crean los módulos correctamente."""
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            skip_eventos=True,
            skip_lecturas=True,
            stdout=StringIO(),
        )

        self.assertEqual(FleetModule.objects.count(), 3)

        # Módulo 01 debe ser CUADRUPLA
        m01 = FleetModule.objects.get(id=1)
        self.assertEqual(m01.module_type, FleetModule.ModuleType.CUADRUPLA)

        # Módulo 45 debe ser TRIPLA (id >= 43)
        m45 = FleetModule.objects.get(id=45)
        self.assertEqual(m45.module_type, FleetModule.ModuleType.TRIPLA)

    def test_import_events_creates_maintenance_events(self):
        """Valida que se crean eventos de mantenimiento con perfiles correctos."""
        # Primero cargar módulos
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            skip_eventos=True,
            skip_lecturas=True,
            stdout=StringIO(),
        )

        # Luego eventos
        call_command(
            "import_legacy_data",
            eventos=str(self.eventos_csv),
            skip_modulos=True,
            skip_lecturas=True,
            stdout=StringIO(),
        )

        self.assertEqual(MaintenanceEvent.objects.count(), 3)

        # Verificar evento IQ
        event_iq = MaintenanceEvent.objects.get(
            fleet_module__id=1, profile__code=MaintenanceProfile.MaintenanceCode.QUINCENAL
        )
        self.assertEqual(event_iq.event_date, date(2025, 1, 1))
        self.assertEqual(event_iq.odometer_km, 1000000)
        self.assertIn("IQ1", event_iq.notes)

        # Verificar perfil Anual
        event_a = MaintenanceEvent.objects.get(
            fleet_module__id=1, profile__code=MaintenanceProfile.MaintenanceCode.ANUAL
        )
        self.assertEqual(event_a.event_date, date(2025, 6, 15))
        self.assertEqual(event_a.odometer_km, 1200000)

    def test_import_readings_creates_odometer_logs(self):
        """Valida que se crean lecturas de odómetro y actualiza km acumulado."""
        # Cargar módulos primero
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            skip_eventos=True,
            skip_lecturas=True,
            stdout=StringIO(),
        )

        # Cargar lecturas
        call_command(
            "import_legacy_data",
            lecturas=str(self.lecturas_csv),
            skip_modulos=True,
            skip_eventos=True,
            stdout=StringIO(),
        )

        self.assertEqual(OdometerLog.objects.count(), 5)

        # Verificar última lectura del módulo 01
        m01 = FleetModule.objects.get(id=1)
        self.assertEqual(m01.total_accumulated_km, 1100000)

        # Verificar logs ordenados
        logs_m01 = OdometerLog.objects.filter(fleet_module=m01).order_by("reading_date")
        self.assertEqual(logs_m01.count(), 3)
        self.assertEqual(logs_m01.first().odometer_reading, 1000000)
        self.assertEqual(logs_m01.last().odometer_reading, 1100000)

        # Verificar cálculo de delta
        log_2 = logs_m01[1]
        self.assertEqual(log_2.daily_delta_km, 50000)  # 1050000 - 1000000

    def test_import_with_invalid_module_skips_event(self):
        """Valida que eventos de módulos inexistentes se omiten sin fallar."""
        # Crear CSV con evento para módulo inexistente (formato SIMAF)
        eventos_invalid_csv = self.temp_path / "test_invalid.csv"
        eventos_invalid_csv.write_text(
            "Id_OT_Simaf;Formaciones;Módulos;OT_Simaf;Ingreso;Tipo_Tarea;Tarea;Km;Fecha_Inicio;Fecha_Fin;Observaciones;Clase_Vehículos\n"
            "1;999;99;9999;Programado;Preventivo;IQ1;1.000.000,00;01/01/2025;02/01/2025;Módulo inexistente;C\n",
            encoding="utf-8"
        )

        # No debe fallar, solo omitir
        call_command(
            "import_legacy_data",
            eventos=str(eventos_invalid_csv),
            skip_modulos=True,
            skip_lecturas=True,
            stdout=StringIO(),
        )

        self.assertEqual(MaintenanceEvent.objects.count(), 0)

    def test_import_full_workflow(self):
        """Test de integración: importa módulos, eventos y lecturas completo."""
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            eventos=str(self.eventos_csv),
            lecturas=str(self.lecturas_csv),
            stdout=StringIO(),
        )

        # Verificar totales
        self.assertEqual(FleetModule.objects.count(), 3)
        self.assertEqual(MaintenanceEvent.objects.count(), 3)
        self.assertEqual(OdometerLog.objects.count(), 5)
        self.assertGreater(MaintenanceProfile.objects.count(), 0)

        # Verificar relaciones FK
        m01 = FleetModule.objects.get(id=1)
        self.assertEqual(m01.maintenance_events.count(), 2)  # IQ + A
        self.assertEqual(m01.odometer_logs.count(), 3)

    def test_clear_option_deletes_existing_data(self):
        """Valida que --clear borra datos previos antes de importar."""
        # Crear datos iniciales
        FleetModule.objects.create(
            id=99, module_type=FleetModule.ModuleType.CUADRUPLA, in_service_date=date(2020, 1, 1)
        )

        self.assertEqual(FleetModule.objects.count(), 1)

        # Importar con --clear
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            skip_eventos=True,
            skip_lecturas=True,
            clear=True,
            stdout=StringIO(),
        )

        # Debe haber borrado el módulo 99 y creado los 3 nuevos
        self.assertEqual(FleetModule.objects.count(), 3)
        self.assertFalse(FleetModule.objects.filter(id=99).exists())

    def test_maintenance_profiles_autocreated(self):
        """Valida que los perfiles de mantenimiento se crean automáticamente."""
        # Cargar módulos y eventos
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            eventos=str(self.eventos_csv),
            skip_lecturas=True,
            stdout=StringIO(),
        )

        # Verificar perfiles creados
        self.assertTrue(
            MaintenanceProfile.objects.filter(
                code=MaintenanceProfile.MaintenanceCode.QUINCENAL
            ).exists()
        )
        self.assertTrue(
            MaintenanceProfile.objects.filter(
                code=MaintenanceProfile.MaintenanceCode.ANUAL
            ).exists()
        )
        self.assertTrue(
            MaintenanceProfile.objects.filter(
                code=MaintenanceProfile.MaintenanceCode.BIMESTRAL
            ).exists()
        )

    def test_odometer_log_computes_delta_correctly(self):
        """Valida que OdometerLog calcula correctamente el delta entre lecturas."""
        # Cargar módulos y lecturas
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            lecturas=str(self.lecturas_csv),
            skip_eventos=True,
            stdout=StringIO(),
        )

        # Verificar deltas del módulo 01
        logs = OdometerLog.objects.filter(fleet_module__id=1).order_by("reading_date")
        
        # Primera lectura no tiene delta (es la primera)
        self.assertIsNone(logs[0].daily_delta_km)
        
        # Segunda lectura: 1050000 - 1000000 = 50000
        self.assertEqual(logs[1].daily_delta_km, 50000)
        
        # Tercera lectura: 1100000 - 1050000 = 50000
        self.assertEqual(logs[2].daily_delta_km, 50000)

    def test_skip_options_work_independently(self):
        """Valida que las opciones --skip-* funcionan correctamente."""
        # Solo módulos
        call_command(
            "import_legacy_data",
            modulos=str(self.modulos_csv),
            skip_eventos=True,
            skip_lecturas=True,
            stdout=StringIO(),
        )
        self.assertEqual(FleetModule.objects.count(), 3)
        self.assertEqual(MaintenanceEvent.objects.count(), 0)
        self.assertEqual(OdometerLog.objects.count(), 0)

        # Solo eventos (requiere módulos previos)
        call_command(
            "import_legacy_data",
            eventos=str(self.eventos_csv),
            skip_modulos=True,
            skip_lecturas=True,
            stdout=StringIO(),
        )
        self.assertEqual(MaintenanceEvent.objects.count(), 3)
        self.assertEqual(OdometerLog.objects.count(), 0)

        # Solo lecturas
        call_command(
            "import_legacy_data",
            lecturas=str(self.lecturas_csv),
            skip_modulos=True,
            skip_eventos=True,
            stdout=StringIO(),
        )
        self.assertEqual(OdometerLog.objects.count(), 5)
