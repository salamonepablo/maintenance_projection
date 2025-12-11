from __future__ import annotations

import math
from datetime import date, timedelta

from django.db import models
from django.utils import timezone


class MaintenanceProfile(models.Model):
    """
    Define ciclos de mantenimiento con disparador dual (tiempo o kilometraje).

    Cada perfil representa un ciclo de mantenimiento (e.g., quincenal, anual).
    """

    class MaintenanceType(models.TextChoices):
        LIVIANO = "LIVIANO", "Liviano"
        PESADO = "PESADO", "Pesado"

    class MaintenanceCode(models.TextChoices):
        QUINCENAL = "IQ", "Inspección quincenal"
        BIMESTRAL = "B", "Bimestral"
        ANUAL = "A", "Anual"
        BIANUAL = "BI", "Bianual"
        PENTANUAL = "P", "Pentanual"
        DECANUAL = "DE", "Decanual"

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(
        max_length=4,
        unique=True,
        choices=MaintenanceCode.choices,
        help_text="Abreviatura normativa del ciclo (p. ej., IQ, B, A, BI, P, DE)",
    )
    maintenance_type = models.CharField(
        max_length=10, choices=MaintenanceType.choices, default=MaintenanceType.LIVIANO
    )
    km_interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Kilometraje máximo permitido antes de la próxima intervención.",
    )
    time_interval_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Cantidad de días máximos antes de la próxima intervención.",
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["maintenance_type", "name"]

    def __str__(self) -> str:  # pragma: no cover - representación simple
        return f"{self.code} - {self.name}"


class FleetModule(models.Model):
    """
    Representa un módulo indivisible de la flota CSR.

    El identificador primario corresponde al número de módulo (01-86).
    """

    class ModuleType(models.TextChoices):
        CUADRUPLA = "CUADRUPLA", "Cuádrupla"
        TRIPLA = "TRIPLA", "Tripla"

    id = models.PositiveSmallIntegerField(primary_key=True)
    module_type = models.CharField(max_length=10, choices=ModuleType.choices)
    in_service_date = models.DateField()
    total_accumulated_km = models.BigIntegerField(default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pragma: no cover - representación simple
        return f"Módulo {self.id:02d} ({self.get_module_type_display()})"

    def update_accumulated_km(self) -> None:
        """Recalcula el kilometraje acumulado según los registros de odómetro."""

        latest_log = self.odometer_logs.order_by("-reading_date", "-id").first()
        if latest_log:
            self.total_accumulated_km = latest_log.odometer_reading
            self.save(update_fields=["total_accumulated_km"])


class MaintenanceEvent(models.Model):
    """Registra una intervención de mantenimiento aplicada a un módulo específico."""

    fleet_module = models.ForeignKey(
        FleetModule, related_name="maintenance_events", on_delete=models.CASCADE
    )
    profile = models.ForeignKey(
        MaintenanceProfile, related_name="events", on_delete=models.PROTECT
    )
    event_date = models.DateField()
    odometer_km = models.PositiveIntegerField(
        help_text="Lectura de odómetro al momento del mantenimiento."
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-event_date", "fleet_module"]
        unique_together = ("fleet_module", "profile", "event_date")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.profile.code} en módulo {self.fleet_module.id:02d} ({self.event_date})"


class OdometerLog(models.Model):
    """Registros transaccionales de lecturas de odómetro por módulo."""

    fleet_module = models.ForeignKey(
        FleetModule, related_name="odometer_logs", on_delete=models.CASCADE
    )
    reading_date = models.DateField()
    odometer_reading = models.PositiveIntegerField(
        help_text="Lectura acumulada de odómetro del módulo en la fecha indicada."
    )
    daily_delta_km = models.IntegerField(
        null=True,
        blank=True,
        help_text="Diferencia de kilómetros recorridos desde la última lectura registrada.",
    )

    class Meta:
        ordering = ["fleet_module", "reading_date", "id"]
        unique_together = ("fleet_module", "reading_date")

    def __str__(self) -> str:  # pragma: no cover
        return f"Lectura {self.odometer_reading} km - módulo {self.fleet_module.id:02d} ({self.reading_date})"

    def compute_daily_delta(self) -> None:
        """Calcula el delta diario comparando con la lectura anterior disponible."""

        previous_log = (
            OdometerLog.objects.filter(
                fleet_module=self.fleet_module, reading_date__lt=self.reading_date
            )
            .order_by("-reading_date", "-id")
            .first()
        )
        if previous_log:
            self.daily_delta_km = self.odometer_reading - previous_log.odometer_reading

    def save(self, *args, **kwargs) -> None:
        """Sobre-escribe el guardado para calcular delta y actualizar acumulado."""

        self.compute_daily_delta()
        super().save(*args, **kwargs)
        self.fleet_module.update_accumulated_km()


class ProjectionService:
    """Servicio auxiliar para proyectar la próxima intervención por disparador dual."""

    def __init__(self, average_window_days: int = 30) -> None:
        self.average_window_days = average_window_days

    def project_next_due(
        self, fleet_module: FleetModule, profile: MaintenanceProfile
    ) -> date | None:
        """
        Retorna la fecha estimada de la próxima intervención considerando:
        - Disparador por tiempo: última intervención + ventana temporal.
        - Disparador por kilometraje: proyección según km pendiente y uso medio diario.

        Si no existe evento previo para el perfil, retorna ``None``.
        """

        last_event = (
            MaintenanceEvent.objects.filter(fleet_module=fleet_module, profile=profile)
            .order_by("-event_date")
            .first()
        )
        if not last_event:
            return None

        time_due_date = None
        if profile.time_interval_days:
            time_due_date = last_event.event_date + timedelta(days=profile.time_interval_days)

        km_due_date = None
        if profile.km_interval:
            km_due_date = self._project_km_due_date(
                fleet_module=fleet_module,
                last_odometer=last_event.odometer_km,
                km_interval=profile.km_interval,
            )

        candidates = [date for date in [time_due_date, km_due_date] if date is not None]
        return min(candidates) if candidates else None

    def _project_km_due_date(
        self, fleet_module: FleetModule, last_odometer: int, km_interval: int
    ) -> date | None:
        """Calcula la fecha en que se alcanzará el km límite del ciclo."""

        target_km = last_odometer + km_interval
        remaining_km = target_km - fleet_module.total_accumulated_km
        if remaining_km <= 0:
            return timezone.now().date()

        average_daily_km = self._estimate_average_daily_km(fleet_module)
        if average_daily_km is None or average_daily_km <= 0:
            return None

        days_needed = math.ceil(remaining_km / average_daily_km)
        return timezone.now().date() + timedelta(days=days_needed)

    def _estimate_average_daily_km(self, fleet_module: FleetModule) -> float | None:
        """
        Estima el uso diario promedio usando la ventana de ``average_window_days``.

        Requiere al menos dos lecturas en la ventana para computar el delta.
        """

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=self.average_window_days)
        logs = list(
            fleet_module.odometer_logs.filter(reading_date__gte=start_date)
            .order_by("reading_date")
            .values_list("reading_date", "odometer_reading")
        )

        if len(logs) < 2:
            return None

        first_date, first_reading = logs[0]
        last_date, last_reading = logs[-1]
        days = max((last_date - first_date).days, 1)
        return (last_reading - first_reading) / days
