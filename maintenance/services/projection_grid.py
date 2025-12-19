"""
Servicio de proyección de mantenimiento para flota CSR.
Implementa lógica de reseteo en cascada idéntica al código VB Materfer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maintenance.models import FleetModule, MaintenanceEvent

@dataclass
class GridCell:
    """Representa una celda en la grilla de proyección"""
    month_date: date
    km_accumulated: int
    intervention_code: str | None = None  # "DA", "P", "BI", "A"
    is_reset_point: bool = False
    exceeds_threshold: bool = False


@dataclass
class ModuleProjectionRow:
    """Representa una fila de proyección para un tipo de mantenimiento"""
    module_number: int
    intervention_type: str  # "DA", "P", "BI", "A"
    last_event_date: date | None
    initial_km: int
    cells: list[GridCell]


class MaintenanceProjectionGrid:
    """
    Genera grilla de proyección de mantenimiento.
    
    Lógica de reseteo en cascada (de VB):
    - DA (Decanual): resetea DA, P, BI, A
    - P (Pentanual): resetea P, BI, A (NO resetea DA)
    - BI (Bianual): resetea BI, A (NO resetea P ni DA)
    - A (Anual): solo resetea A
    """
    
    # Jerarquía de mayor a menor importancia
    HIERARCHY = ["DA", "P", "BI", "A"]
    
    # Umbrales de kilometraje para alertas (colores)
    THRESHOLDS = {
        "DA": 1_500_000,
        "P": 750_000,
        "BI": 375_000,
        "A": 187_500,
    }
    
    # Intervalos normativos
    INTERVALS_KM = {
        "DA": 1_500_000,
        "P": 750_000,
        "BI": 375_000,
        "A": 187_500,
    }
    
    def __init__(self, monthly_km: int = 12_500):
        """
        Args:
            monthly_km: Kilometraje promedio mensual (default: 12.500 km/mes)
        """
        self.monthly_km = monthly_km
    
    def generate_for_module(
        self,
        module: FleetModule,
        months_ahead: int = 24,
        start_date: date | None = None
    ) -> list[ModuleProjectionRow]:
        """
        Genera proyección para un módulo.
        
        Args:
            module: Módulo a proyectar
            months_ahead: Cantidad de meses a proyectar
            start_date: Fecha de inicio (default: hoy)
            
        Returns:
            Lista de 4 filas (DA, P, BI, A) con proyección mes a mes
        """
        if start_date is None:
            start_date = date.today()
        
        # Obtener último evento de cada tipo
        last_events = self._get_last_events_by_type(module)
        
        # Calcular km inicial para cada tipo según lógica de jerarquía
        initial_kms = self._calculate_initial_kms(module, last_events)
        
        # Generar filas de proyección
        rows = []
        for maint_type in self.HIERARCHY:
            row = self._generate_row(
                module=module,
                maint_type=maint_type,
                last_event=last_events.get(maint_type),
                initial_km=initial_kms[maint_type],
                start_date=start_date,
                months_ahead=months_ahead
            )
            rows.append(row)
        
        return rows
    
    def generate_for_all_modules(
        self,
        modules: list[FleetModule],
        months_ahead: int = 24,
        start_date: date | None = None
    ) -> dict[int, list[ModuleProjectionRow]]:
        """
        Genera proyección para múltiples módulos.
        
        Returns:
            Dict con module_number como key y lista de filas como value
        """
        return {
            module.module_number: self.generate_for_module(
                module, months_ahead, start_date
            )
            for module in modules
        }
    
    def _get_last_events_by_type(
        self,
        module: FleetModule
    ) -> dict[str, MaintenanceEvent]:
        """Obtiene el último evento de cada tipo para el módulo"""
        from maintenance.models import MaintenanceEvent
        
        last_events = {}
        for maint_type in self.HIERARCHY:
            event = (
                MaintenanceEvent.objects
                .filter(module=module, maintenance_type=maint_type)
                .order_by('-date', '-odometer_reading')
                .first()
            )
            if event:
                last_events[maint_type] = event
        
        return last_events
    
    def _calculate_initial_kms(
        self,
        module: FleetModule,
        last_events: dict[str, MaintenanceEvent]
    ) -> dict[str, int]:
        """
        Calcula km inicial para cada tipo según lógica de jerarquía.
        
        Lógica VB:
        - Si un evento de mayor jerarquía es más reciente, "pisa" los de menor
        - DA: siempre desde 0 km (no hay DA previas)
        - P: desde última P, PERO si hubo DA posterior, desde DA
        - BI: desde última BI, PERO si hubo P o DA posterior, desde el más reciente
        - A: desde última A, PERO si hubo BI, P o DA posterior, desde el más reciente
        """
        initial_kms = {}
        
        # DA siempre desde 0 (aún no hay eventos DA)
        initial_kms["DA"] = module.total_accumulated_km or 0
        
        # Para cada tipo, verificar si hay un evento superior más reciente
        for idx, maint_type in enumerate(self.HIERARCHY[1:], start=1):
            # Tipos superiores en jerarquía
            superior_types = self.HIERARCHY[:idx]
            
            # Fecha del último evento de este tipo
            current_event = last_events.get(maint_type)
            current_date = current_event.date if current_event else None
            
            # Buscar el evento superior más reciente
            most_recent_superior = None
            most_recent_superior_date = None
            
            for sup_type in superior_types:
                sup_event = last_events.get(sup_type)
                if sup_event:
                    sup_date = sup_event.date
                    # Si no hay fecha actual O el superior es más reciente
                    if (current_date is None or 
                        sup_date > current_date or
                        (sup_date == current_date and 
                         self.HIERARCHY.index(sup_type) < self.HIERARCHY.index(maint_type))):
                        if (most_recent_superior_date is None or 
                            sup_date > most_recent_superior_date):
                            most_recent_superior = sup_event
                            most_recent_superior_date = sup_date
            
            # Determinar km inicial
            if most_recent_superior:
                # Hay un evento superior más reciente: usar sus km
                initial_kms[maint_type] = self._calculate_km_since_event(
                    module, most_recent_superior
                )
            elif current_event:
                # Usar km desde último evento de este tipo
                initial_kms[maint_type] = self._calculate_km_since_event(
                    module, current_event
                )
            else:
                # No hay eventos: usar km total del módulo
                initial_kms[maint_type] = module.total_accumulated_km or 0
        
        return initial_kms
    
    def _calculate_km_since_event(
        self,
        module: FleetModule,
        event: MaintenanceEvent
    ) -> int:
        """Calcula km recorridos desde un evento"""
        from maintenance.models import OdometerLog
        
        # Sumar todos los km desde la fecha del evento
        logs_since = OdometerLog.objects.filter(
            module=module,
            reading_date__gt=event.date
        ).order_by('reading_date')
        
        km_since = sum(log.daily_delta_km or 0 for log in logs_since)
        return int(km_since)
    
    def _generate_row(
        self,
        module: FleetModule,
        maint_type: str,
        last_event: MaintenanceEvent | None,
        initial_km: int,
        start_date: date,
        months_ahead: int
    ) -> ModuleProjectionRow:
        """Genera una fila de proyección para un tipo de mantenimiento"""
        cells = []
        accumulated_km = initial_km
        threshold = self.THRESHOLDS[maint_type]
        
        for month_offset in range(1, months_ahead + 1):
            month_date = self._add_months(start_date, month_offset)
            accumulated_km += self.monthly_km
            
            # Verificar si excede umbral
            exceeds = accumulated_km >= threshold
            
            # Determinar si hay intervención en este mes
            intervention = None
            is_reset = False
            
            # Si excede el umbral del intervalo, marcar intervención
            if accumulated_km >= self.INTERVALS_KM[maint_type]:
                intervention = maint_type
                is_reset = True
                # Resetear km (como en VB: poner 0 y empezar de nuevo)
                accumulated_km = 0
            
            cell = GridCell(
                month_date=month_date,
                km_accumulated=accumulated_km,
                intervention_code=intervention,
                is_reset_point=is_reset,
                exceeds_threshold=exceeds
            )
            cells.append(cell)
        
        return ModuleProjectionRow(
            module_number=module.module_number,
            intervention_type=maint_type,
            last_event_date=last_event.date if last_event else None,
            initial_km=initial_km,
            cells=cells
        )
    
    @staticmethod
    def _add_months(base_date: date, months: int) -> date:
        """Suma meses a una fecha"""
        month = base_date.month - 1 + months
        year = base_date.year + month // 12
        month = month % 12 + 1
        day = min(base_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)
    
    def export_to_dict(
        self,
        projections: dict[int, list[ModuleProjectionRow]]
    ) -> dict:
        """
        Exporta proyecciones a formato dict para JSON/template.
        
        Returns:
            Dict con estructura lista para renderizar
        """
        result = {
            "monthly_km": self.monthly_km,
            "modules": []
        }
        
        for module_number in sorted(projections.keys()):
            rows = projections[module_number]
            module_data = {
                "module_number": module_number,
                "rows": []
            }
            
            for row in rows:
                row_data = {
                    "intervention_type": row.intervention_type,
                    "last_event_date": row.last_event_date.isoformat() if row.last_event_date else None,
                    "initial_km": row.initial_km,
                    "cells": [
                        {
                            "month": cell.month_date.strftime("%b %y"),
                            "km": cell.km_accumulated,
                            "intervention": cell.intervention_code,
                            "is_reset": cell.is_reset_point,
                            "exceeds": cell.exceeds_threshold,
                        }
                        for cell in row.cells
                    ]
                }
                module_data["rows"].append(row_data)
            
            result["modules"].append(module_data)
        
        return result
