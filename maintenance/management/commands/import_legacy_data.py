"""
Management Command: import_legacy_data

Importa datos históricos de flota CSR desde archivos CSV legacy.
Carga módulos, eventos de mantenimiento y lecturas de odómetro.

Uso:
    python manage.py import_legacy_data --modulos context/CSR_Modulos.csv \
        --eventos context/CSR_MantEvents.csv \
        --lecturas context/CSR_LecturasKms.csv
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm

from maintenance.models import FleetModule, MaintenanceEvent, MaintenanceProfile, OdometerLog


class Command(BaseCommand):
    """Comando de Django para importar datos legacy de la flota CSR."""

    help = "Importa datos históricos de módulos, eventos de mantenimiento y lecturas de odómetro desde CSVs"

    def add_arguments(self, parser):
        """Define los argumentos del comando."""
        parser.add_argument(
            "--modulos",
            type=str,
            default="context/CSR_Modulos.csv",
            help="Ruta al CSV de módulos (default: context/CSR_Modulos.csv)",
        )
        parser.add_argument(
            "--eventos",
            type=str,
            default="context/CSR_MantEvents.csv",
            help="Ruta al CSV de eventos de mantenimiento (default: context/CSR_MantEvents.csv)",
        )
        parser.add_argument(
            "--lecturas",
            type=str,
            default="context/CSR_LecturasKms.csv",
            help="Ruta al CSV de lecturas de odómetro (default: context/CSR_LecturasKms.csv)",
        )
        parser.add_argument(
            "--skip-modulos",
            action="store_true",
            help="Omite la carga de módulos (si ya existen)",
        )
        parser.add_argument(
            "--skip-eventos",
            action="store_true",
            help="Omite la carga de eventos de mantenimiento",
        )
        parser.add_argument(
            "--skip-lecturas",
            action="store_true",
            help="Omite la carga de lecturas de odómetro",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Borra todos los datos existentes antes de importar (PELIGRO: irreversible)",
        )

    def handle(self, *args, **options):
        """Ejecuta el proceso ETL completo."""
        self.stdout.write(self.style.SUCCESS("=== Iniciando importación de datos legacy CSR ==="))

        # Validar rutas
        modulos_path = Path(options["modulos"])
        eventos_path = Path(options["eventos"])
        lecturas_path = Path(options["lecturas"])

        if not options["skip_modulos"] and not modulos_path.exists():
            raise CommandError(f"Archivo de módulos no encontrado: {modulos_path}")
        if not options["skip_eventos"] and not eventos_path.exists():
            raise CommandError(f"Archivo de eventos no encontrado: {eventos_path}")
        if not options["skip_lecturas"] and not lecturas_path.exists():
            raise CommandError(f"Archivo de lecturas no encontrado: {lecturas_path}")

        # Borrar datos si se solicita
        if options["clear"]:
            self._clear_existing_data()

        # Ejecutar carga en orden (respetando FK)
        with transaction.atomic():
            if not options["skip_modulos"]:
                self._load_fleet_modules(modulos_path)

            if not options["skip_eventos"]:
                self._load_maintenance_events(eventos_path)

            if not options["skip_lecturas"]:
                self._load_odometer_readings(lecturas_path)

        self.stdout.write(self.style.SUCCESS("\n✓ Importación completada exitosamente"))

    def _clear_existing_data(self):
        """Borra todos los datos de la base antes de importar."""
        self.stdout.write(self.style.WARNING("\n⚠️  Borrando datos existentes..."))
        
        counts = {
            "OdometerLog": OdometerLog.objects.count(),
            "MaintenanceEvent": MaintenanceEvent.objects.count(),
            "FleetModule": FleetModule.objects.count(),
        }
        
        OdometerLog.objects.all().delete()
        MaintenanceEvent.objects.all().delete()
        FleetModule.objects.all().delete()
        
        self.stdout.write(
            f"  Borrados: {counts['OdometerLog']} lecturas, "
            f"{counts['MaintenanceEvent']} eventos, "
            f"{counts['FleetModule']} módulos"
        )

    def _load_fleet_modules(self, csv_path: Path):
        """
        Carga módulos de flota desde CSV.
        
        Formato esperado:
        - FORMACION, MODULO, MC1, R1, R2, MC2
        - El campo MODULO contiene el ID (01-86)
        """
        self.stdout.write(self.style.HTTP_INFO("\n1️⃣  Cargando módulos de flota..."))
        
        try:
            df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, sep=";", encoding="latin-1")

        if "MODULO" not in df.columns:
            raise CommandError(f"CSV de módulos debe contener columna 'MODULO': {df.columns.tolist()}")

        modules_created = 0
        modules_updated = 0

        for _, row in tqdm(df.iterrows(), total=len(df), desc="Módulos", unit="mod"):
            try:
                module_id = int(row["MODULO"])
                
                # Determinar tipo de formación según ID
                if module_id <= 42:
                    module_type = FleetModule.ModuleType.CUADRUPLA
                else:
                    module_type = FleetModule.ModuleType.TRIPLA

                # Fecha de puesta en servicio: asumimos 2015-01-01 si no hay dato
                # (ajustar según datos reales disponibles)
                in_service = datetime(2015, 1, 1).date()

                module, created = FleetModule.objects.update_or_create(
                    id=module_id,
                    defaults={
                        "module_type": module_type,
                        "in_service_date": in_service,
                        "total_accumulated_km": 0,  # Se actualiza con lecturas
                    },
                )

                if created:
                    modules_created += 1
                else:
                    modules_updated += 1

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  Error procesando módulo {row.get('MODULO', 'N/A')}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Módulos: {modules_created} creados, {modules_updated} actualizados"
            )
        )

    def _load_maintenance_events(self, csv_path: Path):
        """
        Carga eventos de mantenimiento desde CSV.
        
        Formato esperado:
        - Id_Mantenimiento, Módulo, Tipo_Mantenimiento, Fecha, Kilometraje, Observaciones
        """
        self.stdout.write(self.style.HTTP_INFO("\n2️⃣  Cargando eventos de mantenimiento..."))

        try:
            df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, sep=";", encoding="latin-1")

        # Mapeo de códigos del CSV a códigos del modelo
        code_mapping = {
            "IQ": MaintenanceProfile.MaintenanceCode.QUINCENAL,
            "B": MaintenanceProfile.MaintenanceCode.BIMESTRAL,
            "A": MaintenanceProfile.MaintenanceCode.ANUAL,
            "BI": MaintenanceProfile.MaintenanceCode.BIANUAL,
            "P": MaintenanceProfile.MaintenanceCode.PENTANUAL,
            "DE": MaintenanceProfile.MaintenanceCode.DECANUAL,
        }

        events_created = 0
        events_skipped = 0

        for _, row in tqdm(df.iterrows(), total=len(df), desc="Eventos", unit="evt"):
            try:
                # Extraer módulo (puede venir como "M01" o "01")
                module_str = str(row.get("Módulo", "")).strip().upper()
                module_id = int(module_str.replace("M", ""))

                # Buscar módulo
                try:
                    fleet_module = FleetModule.objects.get(id=module_id)
                except FleetModule.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️  Módulo {module_id} no existe, evento omitido")
                    )
                    events_skipped += 1
                    continue

                # Tipo de mantenimiento
                tipo_code = str(row.get("Tipo_Mantenimiento", "")).strip().upper()
                profile_code = code_mapping.get(tipo_code)

                if not profile_code:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️  Código de mantenimiento desconocido: {tipo_code}, evento omitido"
                        )
                    )
                    events_skipped += 1
                    continue

                # Buscar o crear perfil de mantenimiento
                profile, _ = MaintenanceProfile.objects.get_or_create(
                    code=profile_code,
                    defaults={
                        "name": dict(MaintenanceProfile.MaintenanceCode.choices)[profile_code],
                        "maintenance_type": MaintenanceProfile.MaintenanceType.LIVIANO
                        if profile_code in ["IQ", "B"]
                        else MaintenanceProfile.MaintenanceType.PESADO,
                    },
                )

                # Parsear fecha (formato DD/MM/YYYY)
                fecha_str = str(row.get("Fecha", "")).strip()
                event_date = datetime.strptime(fecha_str, "%d/%m/%Y").date()

                # Kilometraje (puede venir con puntos como separadores de miles)
                km_str = str(row.get("Kilometraje", "0")).replace(".", "").replace(",", ".")
                odometer_km = int(float(km_str))

                # Observaciones
                notes = str(row.get("Observaciones", "")).strip()

                # Crear evento
                MaintenanceEvent.objects.get_or_create(
                    fleet_module=fleet_module,
                    profile=profile,
                    event_date=event_date,
                    defaults={
                        "odometer_km": odometer_km,
                        "notes": notes,
                    },
                )

                events_created += 1

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Error procesando evento {row.get('Id_Mantenimiento', 'N/A')}: {e}"
                    )
                )
                events_skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Eventos: {events_created} creados, {events_skipped} omitidos"
            )
        )

    def _load_odometer_readings(self, csv_path: Path):
        """
        Carga lecturas de odómetro desde CSV.
        
        Formato esperado:
        - Id_Kilometrajes, Módulo, kilometraje, Fecha
        
        Importante: El CSV debe procesarse ordenado por fecha ascendente para calcular deltas correctos.
        """
        self.stdout.write(self.style.HTTP_INFO("\n3️⃣  Cargando lecturas de odómetro..."))

        try:
            df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, sep=";", encoding="latin-1")

        # Parsear fechas y ordenar cronológicamente
        df["Fecha_parsed"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
        df = df.sort_values(["Módulo", "Fecha_parsed"])

        readings_created = 0
        readings_skipped = 0

        for _, row in tqdm(df.iterrows(), total=len(df), desc="Lecturas", unit="lec"):
            try:
                # Extraer módulo
                module_str = str(row.get("Módulo", "")).strip().upper()
                module_id = int(module_str.replace("M", ""))

                # Buscar módulo
                try:
                    fleet_module = FleetModule.objects.get(id=module_id)
                except FleetModule.DoesNotExist:
                    readings_skipped += 1
                    continue

                # Fecha
                reading_date = row["Fecha_parsed"].date()

                # Kilometraje (formato: "1.285.885,00" → 1285885)
                km_str = str(row.get("kilometraje", "0")).replace(".", "").replace(",", ".")
                odometer_reading = int(float(km_str))

                # Crear lectura (el método save() del modelo ya calcula el delta y actualiza acumulado)
                OdometerLog.objects.get_or_create(
                    fleet_module=fleet_module,
                    reading_date=reading_date,
                    defaults={"odometer_reading": odometer_reading},
                )

                readings_created += 1

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Error procesando lectura {row.get('Id_Kilometrajes', 'N/A')}: {e}"
                    )
                )
                readings_skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Lecturas: {readings_created} creadas, {readings_skipped} omitidas"
            )
        )

        # Actualizar km acumulado final para todos los módulos
        self.stdout.write(self.style.HTTP_INFO("\n📊 Actualizando kilometrajes acumulados..."))
        for module in FleetModule.objects.all():
            module.update_accumulated_km()
        self.stdout.write(self.style.SUCCESS("  ✓ Kilometrajes actualizados"))
