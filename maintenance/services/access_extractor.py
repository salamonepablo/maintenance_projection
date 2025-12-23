"""
Access Data Extractor - Adaptado a estructura real de DB_CCEE_Mantenimiento.

Este servicio extrae datos de Access para sincronizar con Django.

Fuentes de datos:
- A_00_Kilometrajes: Lecturas de odómetro
- A_00_OT_Simaf: Eventos de mantenimiento
- 01_Coches: Maestro de coches
- 11_CambioCoches: Relación Coche-Módulo
- 12_CambioMódulos: Relación Módulo-Formación

Filtro: Solo módulos CSR (Módulo LIKE 'M%')
"""
from __future__ import annotations

import pyodbc
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class ModuleData:
    """Datos de un módulo CSR."""
    module_number: int  # 1, 2, 3... (extraído de M01, M02...)
    module_id: str  # M01, M02, M03...
    formation: Optional[str] = None  # F120, F121...
    cabin_position: Optional[str] = None  # A, B
    coaches: Optional[List[str]] = None  # [5001, 5002, 5601, 5801]


@dataclass
class MaintenanceEventData:
    """Datos de un evento de mantenimiento."""
    module_id: str  # M01, M02...
    maintenance_type: str  # IQ, B, A, BI, P, DE
    event_date: date
    odometer_km: int
    raw_task: str  # Tarea original de Access


@dataclass
class OdometerReadingData:
    """Datos de una lectura de odómetro."""
    module_id: str  # M01, M02...
    reading_date: date
    odometer_reading: int


class AccessExtractor:
    """Extractor de datos de Access para flota CSR."""
    
    # Mapeo de ciclos Access → Django/CNRT
    CYCLE_MAPPING = {
        'IQ': 'IQ',  # Quincenal
        'IB': 'B',   # Bimestral
        'AN': 'A',   # Anual
        'BA': 'BI',  # Bianual
        'RS': 'P',   # Pentanual
        # DE no existe aún en Access
    }
    
    def __init__(self, connection_string: str):
        """
        Inicializa el extractor.
        
        Args:
            connection_string: String de conexión ODBC a Access
        """
        self.connection_string = connection_string
        self.conn: Optional[pyodbc.Connection] = None
    
    def connect(self) -> bool:
        """
        Establece conexión con Access.
        
        Returns:
            True si conectó exitosamente
        """
        try:
            self.conn = pyodbc.connect(self.connection_string)
            return True
        except pyodbc.Error as e:
            print(f"Error conectando a Access: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    @staticmethod
    def extract_module_number(module_id: str) -> Optional[int]:
        """
        Extrae el número de un módulo.
        
        Args:
            module_id: ID del módulo (ej: 'M01', 'M10', 'M45')
        
        Returns:
            Número del módulo (1, 10, 45) o None si no es válido
        """
        match = re.match(r'M(\d+)', module_id)
        if match:
            return int(match.group(1))
        return None
    
    @staticmethod
    def normalize_maintenance_type(raw_task: str) -> Optional[str]:
        """
        Normaliza el tipo de mantenimiento desde Access a Django.
        
        Args:
            raw_task: Tarea de Access (ej: 'IQ', 'IB', 'AN1', 'BA2')
        
        Returns:
            Tipo normalizado (IQ, B, A, BI, P, DE) o None si no es válido
        """
        if not raw_task:
            return None
        
        # Extraer primeros 2 caracteres
        task_code = raw_task[:2].upper()
        
        # Mapear según tabla de equivalencias
        return AccessExtractor.CYCLE_MAPPING.get(task_code)
    
    def get_active_modules(self) -> List[ModuleData]:
        """
        Obtiene lista de módulos CSR activos.
        
        Extrae módulos únicos de A_00_Kilometrajes y A_00_OT_Consulta,
        y los enriquece con información de formación.
        
        Returns:
            Lista de ModuleData
        """
        if not self.conn:
            raise RuntimeError("No hay conexión activa")
        
        cursor = self.conn.cursor()
        modules_dict: Dict[str, ModuleData] = {}
        
        # Obtener módulos de kilometrajes
        try:
            cursor.execute("""
                SELECT DISTINCT Módulo
                FROM A_00_Kilometrajes
                WHERE Módulo LIKE 'M%'
                ORDER BY Módulo
            """)
            
            for row in cursor.fetchall():
                module_id = row[0].strip() if row[0] else None
                if module_id:
                    module_num = self.extract_module_number(module_id)
                    if module_num:
                        modules_dict[module_id] = ModuleData(
                            module_number=module_num,
                            module_id=module_id
                        )
        except pyodbc.Error as e:
            print(f"Error obteniendo módulos de kilometrajes: {e}")
        
        # Obtener módulos de mantenimientos
        try:
            cursor.execute("""
                SELECT DISTINCT Módulo
                FROM A_00_OT_Simaf
                WHERE Módulo LIKE 'M%'
            """)
            
            for row in cursor.fetchall():
                module_id = row[0].strip() if row[0] else None
                if module_id and module_id not in modules_dict:
                    module_num = self.extract_module_number(module_id)
                    if module_num:
                        modules_dict[module_id] = ModuleData(
                            module_number=module_num,
                            module_id=module_id
                        )
        except pyodbc.Error as e:
            print(f"Error obteniendo módulos de mantenimientos: {e}")
        
        # Enriquecer con información de formación (última asignación)
        for module_id in modules_dict.keys():
            try:
                cursor.execute("""
                    SELECT TOP 1 Formación, Cabina
                    FROM [12_CambioMódulos]
                    WHERE Módulo = ?
                    ORDER BY Fecha DESC
                """, (module_id,))
                
                row = cursor.fetchone()
                if row:
                    modules_dict[module_id].formation = row[0]
                    modules_dict[module_id].cabin_position = row[1]
            except pyodbc.Error:
                pass  # No crítico si no hay datos de formación
        
        cursor.close()
        
        return list(modules_dict.values())
    
    def get_maintenance_events(
        self,
        module_id: Optional[str] = None,
        since_date: Optional[date] = None
    ) -> List[MaintenanceEventData]:
        """
        Obtiene eventos de mantenimiento desde A_00_OT_Simaf.
        
        Args:
            module_id: Filtrar por módulo específico (ej: 'M01')
            since_date: Obtener solo eventos desde esta fecha
        
        Returns:
            Lista de MaintenanceEventData
        """
        if not self.conn:
            raise RuntimeError("No hay conexión activa")
        
        cursor = self.conn.cursor()
        events = []
        
        # Construir query
        query = """
            SELECT Módulo, Tarea, Km, Fecha_Fin
            FROM A_00_OT_Simaf
            WHERE Módulo LIKE 'M%'
        """
        params = []
        
        if module_id:
            query += " AND Módulo = ?"
            params.append(module_id)
        
        if since_date:
            query += " AND Fecha_Fin >= ?"
            params.append(since_date)
        
        query += " ORDER BY Fecha_Fin DESC"
        
        try:
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                module = row[0].strip() if row[0] else None
                raw_task = row[1].strip() if row[1] else None
                km = row[2] if row[2] is not None else 0
                fecha_fin = row[3]
                
                if not module or not raw_task or not fecha_fin:
                    continue
                
                # Normalizar tipo de mantenimiento
                maint_type = self.normalize_maintenance_type(raw_task)
                if not maint_type:
                    continue  # Saltar tipos no reconocidos
                
                # Convertir fecha
                event_date = fecha_fin.date() if isinstance(fecha_fin, datetime) else fecha_fin
                
                events.append(MaintenanceEventData(
                    module_id=module,
                    maintenance_type=maint_type,
                    event_date=event_date,
                    odometer_km=int(km),
                    raw_task=raw_task
                ))
        
        except pyodbc.Error as e:
            print(f"Error obteniendo eventos de mantenimiento: {e}")
        
        finally:
            cursor.close()
        
        return events
    
    def get_odometer_readings(
        self,
        module_id: Optional[str] = None,
        since_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[OdometerReadingData]:
        """
        Obtiene lecturas de odómetro desde A_00_Kilometrajes.
        
        Args:
            module_id: Filtrar por módulo específico
            since_date: Obtener solo lecturas desde esta fecha
            limit: Límite de registros (más recientes primero)
        
        Returns:
            Lista de OdometerReadingData
        """
        if not self.conn:
            raise RuntimeError("No hay conexión activa")
        
        cursor = self.conn.cursor()
        readings = []
        
        # Construir query
        query_parts = ["SELECT"]
        if limit:
            query_parts.append(f"TOP {limit}")
        
        query_parts.append("Módulo, kilometraje, Fecha")
        query_parts.append("FROM A_00_Kilometrajes")
        query_parts.append("WHERE Módulo LIKE 'M%'")
        
        params = []
        
        if module_id:
            query_parts.append("AND Módulo = ?")
            params.append(module_id)
        
        if since_date:
            query_parts.append("AND Fecha >= ?")
            params.append(since_date)
        
        query_parts.append("ORDER BY Fecha DESC")
        
        query = " ".join(query_parts)
        
        try:
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                module = row[0].strip() if row[0] else None
                kilometraje = row[1] if row[1] is not None else 0
                fecha = row[2]
                
                if not module or not fecha:
                    continue
                
                # Convertir fecha
                reading_date = fecha.date() if isinstance(fecha, datetime) else fecha
                
                readings.append(OdometerReadingData(
                    module_id=module,
                    reading_date=reading_date,
                    odometer_reading=int(kilometraje)
                ))
        
        except pyodbc.Error as e:
            print(f"Error obteniendo lecturas de odómetro: {e}")
        
        finally:
            cursor.close()
        
        return readings
    
    def get_latest_odometer_reading(self, module_id: str) -> Optional[int]:
        """
        Obtiene la última lectura de odómetro de un módulo.
        
        Args:
            module_id: ID del módulo (ej: 'M01')
        
        Returns:
            Kilometraje o None si no hay lecturas
        """
        readings = self.get_odometer_readings(
            module_id=module_id,
            limit=1
        )
        
        return readings[0].odometer_reading if readings else None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión y retorna estadísticas básicas.
        
        Returns:
            Dict con información de la conexión
        """
        if not self.conn:
            if not self.connect():
                return {"connected": False, "error": "No se pudo conectar"}
        
        cursor = self.conn.cursor()
        stats = {"connected": True}
        
        try:
            # Contar módulos
            cursor.execute("""
                SELECT COUNT(DISTINCT Módulo)
                FROM A_00_Kilometrajes
                WHERE Módulo LIKE 'M%'
            """)
            stats["modules_count"] = cursor.fetchone()[0]
            
            # Contar eventos
            cursor.execute("""
                SELECT COUNT(*)
                FROM A_00_OT_Simaf
                WHERE Módulo LIKE 'M%'
            """)
            stats["events_count"] = cursor.fetchone()[0]
            
            # Contar lecturas
            cursor.execute("""
                SELECT COUNT(*)
                FROM A_00_Kilometrajes
                WHERE Módulo LIKE 'M%'
            """)
            stats["readings_count"] = cursor.fetchone()[0]
            
        except pyodbc.Error as e:
            stats["error"] = str(e)
        
        finally:
            cursor.close()
        
        return stats


# Ejemplo de uso
if __name__ == '__main__':
    # Connection string de ejemplo
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=G:\Material Rodante\1-Servicio Eléctrico\DB'
        r'\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb;'
        'PWD=0733;'
        'ReadOnly=1;'
    )
    
    with AccessExtractor(conn_str) as extractor:
        # Test de conexión
        stats = extractor.test_connection()
        print("Estadísticas de conexión:")
        print(f"  Módulos CSR: {stats.get('modules_count', 0)}")
        print(f"  Eventos: {stats.get('events_count', 0)}")
        print(f"  Lecturas: {stats.get('readings_count', 0)}")
        
        # Obtener módulos
        modules = extractor.get_active_modules()
        print(f"\nMódulos activos: {len(modules)}")
        for mod in modules[:5]:
            print(f"  {mod.module_id} (#{mod.module_number})")
