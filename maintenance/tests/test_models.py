"""
Tests unitarios para los modelos de mantenimiento.

Valida comportamiento de FleetModule, OdometerLog, MaintenanceEvent y ProjectionService.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from maintenance.models import (
    FleetModule,
    MaintenanceEvent,
    MaintenanceProfile,
    OdometerLog,
    ProjectionService,
)


class FleetModuleTests(TestCase):
    """Tests para el modelo FleetModule."""

    def test_create_fleet_module(self):
        """Valida creación básica de módulo."""
        module = FleetModule.objects.create(
            id=1,
            module_type=FleetModule.ModuleType.CUADRUPLA,
            in_service_date=date(2015, 1, 1),
        )
        self.assertEqual(module.total_accumulated_km, 0)
        self.assertEqual(str(module), "Módulo 01 (Cuádrupla)")

    def test_update_accumulated_km_from_latest_log(self):
        """Valida que update_accumulated_km toma la última lectura."""
        module = FleetModule.objects.create(
            id=1,
            module_type=FleetModule.ModuleType.CUADRUPLA,
            in_service_date=date(2015, 1, 1),
        )

        OdometerLog.objects.create(
            fleet_module=module, reading_date=date(2025, 1, 1), odometer_reading=1000000
        )
        OdometerLog.objects.create(
            fleet_module=module, reading_date=date(2025, 1, 15), odometer_reading=1050000
        )

        module.update_accumulated_km()
        self.assertEqual(module.total_accumulated_km, 1050000)


class OdometerLogTests(TestCase):
    """Tests para el modelo OdometerLog."""

    def setUp(self):
        """Crea módulo de prueba."""
        self.module = FleetModule.objects.create(
            id=1,
            module_type=FleetModule.ModuleType.CUADRUPLA,
            in_service_date=date(2015, 1, 1),
        )

    def test_first_log_has_no_delta(self):
        """Primera lectura no tiene delta (no hay lectura previa)."""
        log = OdometerLog.objects.create(
            fleet_module=self.module, reading_date=date(2025, 1, 1), odometer_reading=1000000
        )
        self.assertIsNone(log.daily_delta_km)

    def test_second_log_computes_delta(self):
        """Segunda lectura calcula delta contra primera."""
        OdometerLog.objects.create(
            fleet_module=self.module, reading_date=date(2025, 1, 1), odometer_reading=1000000
        )
        log2 = OdometerLog.objects.create(
            fleet_module=self.module, reading_date=date(2025, 1, 15), odometer_reading=1050000
        )
        self.assertEqual(log2.daily_delta_km, 50000)

    def test_save_updates_module_accumulated_km(self):
        """Guardar log actualiza automáticamente el km acumulado del módulo."""
        OdometerLog.objects.create(
            fleet_module=self.module, reading_date=date(2025, 1, 1), odometer_reading=1000000
        )

        self.module.refresh_from_db()
        self.assertEqual(self.module.total_accumulated_km, 1000000)


class MaintenanceEventTests(TestCase):
    """Tests para el modelo MaintenanceEvent."""

    def setUp(self):
        """Crea módulo y perfil de prueba."""
        self.module = FleetModule.objects.create(
            id=1,
            module_type=FleetModule.ModuleType.CUADRUPLA,
            in_service_date=date(2015, 1, 1),
        )
        self.profile = MaintenanceProfile.objects.create(
            name="Inspección Quincenal",
            code=MaintenanceProfile.MaintenanceCode.QUINCENAL,
            km_interval=5000,
            time_interval_days=15,
        )

    def test_create_maintenance_event(self):
        """Valida creación de evento de mantenimiento."""
        event = MaintenanceEvent.objects.create(
            fleet_module=self.module,
            profile=self.profile,
            event_date=date(2025, 1, 1),
            odometer_km=1000000,
            notes="Inspección realizada",
        )
        self.assertEqual(str(event), "IQ en módulo 01 (2025-01-01)")


class MaintenanceProfileTests(TestCase):
    """Tests para el modelo MaintenanceProfile."""

    def test_profile_with_time_and_km(self):
        """Perfil con ambos disparadores."""
        profile = MaintenanceProfile.objects.create(
            name="Inspección Quincenal",
            code=MaintenanceProfile.MaintenanceCode.QUINCENAL,
            km_interval=5000,
            time_interval_days=15,
            maintenance_type=MaintenanceProfile.MaintenanceType.LIVIANO,
        )
        self.assertEqual(profile.km_interval, 5000)
        self.assertEqual(profile.time_interval_days, 15)
        self.assertEqual(str(profile), "IQ - Inspección Quincenal")


class ProjectionServiceTests(TestCase):
    """Tests para el servicio de proyección."""

    def setUp(self):
        """Configura módulo, perfil y lecturas de prueba."""
        self.module = FleetModule.objects.create(
            id=1,
            module_type=FleetModule.ModuleType.CUADRUPLA,
            in_service_date=date(2015, 1, 1),
            total_accumulated_km=1050000,
        )

        self.profile = MaintenanceProfile.objects.create(
            name="Inspección Quincenal",
            code=MaintenanceProfile.MaintenanceCode.QUINCENAL,
            km_interval=5000,
            time_interval_days=15,
            maintenance_type=MaintenanceProfile.MaintenanceType.LIVIANO,
        )

        # Último evento hace 10 días con 1045000 km
        MaintenanceEvent.objects.create(
            fleet_module=self.module,
            profile=self.profile,
            event_date=timezone.now().date() - timedelta(days=10),
            odometer_km=1045000,
        )

        # Crear lecturas para estimar promedio diario
        base_date = timezone.now().date() - timedelta(days=30)
        for i in range(30):
            OdometerLog.objects.create(
                fleet_module=self.module,
                reading_date=base_date + timedelta(days=i),
                odometer_reading=1020000 + (i * 1000),  # 1000 km/día
            )

        self.service = ProjectionService(average_window_days=30)

    def test_project_next_due_returns_date(self):
        """Proyección devuelve una fecha futura."""
        next_due = self.service.project_next_due(self.module, self.profile)
        self.assertIsNotNone(next_due)
        self.assertIsInstance(next_due, date)

    def test_project_next_due_without_previous_event_returns_none(self):
        """Sin evento previo, proyección devuelve None."""
        new_profile = MaintenanceProfile.objects.create(
            name="Revisión Anual",
            code=MaintenanceProfile.MaintenanceCode.ANUAL,
            km_interval=50000,
            time_interval_days=365,
        )
        next_due = self.service.project_next_due(self.module, new_profile)
        self.assertIsNone(next_due)

    def test_project_uses_minimum_of_time_and_km_triggers(self):
        """Proyección usa el mínimo entre disparador tiempo y km."""
        # Disparador tiempo: último evento + 15 días = en 5 días
        # Disparador km: 5000 km restantes / ~1000 km/día = en ~5 días
        next_due = self.service.project_next_due(self.module, self.profile)
        
        # Debe estar cerca de hoy + 5 días (margen de ±5 días por variaciones)
        expected = timezone.now().date() + timedelta(days=5)
        self.assertLessEqual(abs((next_due - expected).days), 5)

    def test_estimate_average_daily_km_with_sufficient_data(self):
        """Estima promedio diario con datos suficientes."""
        avg = self.service._estimate_average_daily_km(self.module)
        self.assertIsNotNone(avg)
        self.assertAlmostEqual(avg, 1000.0, delta=50)  # ~1000 km/día

    def test_estimate_average_daily_km_with_insufficient_data_returns_none(self):
        """Sin lecturas suficientes, devuelve None."""
        new_module = FleetModule.objects.create(
            id=2,
            module_type=FleetModule.ModuleType.TRIPLA,
            in_service_date=date(2015, 1, 1),
        )
        avg = self.service._estimate_average_daily_km(new_module)
        self.assertIsNone(avg)
