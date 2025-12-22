"""
Script de exploración de base de datos Access.

Este script se conecta a una BD Access y genera un reporte completo:
- Lista de tablas y consultas
- Estructura de cada tabla (columnas, tipos)
- Primeras filas de datos de ejemplo
- Estadísticas (conteo de registros)
"""
from __future__ import annotations

import pyodbc
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime


class AccessExplorer:
    """Explorador de base de datos Microsoft Access."""
    
    def __init__(self, access_db_path: str):
        """
        Inicializa el explorador.
        
        Args:
            access_db_path: Ruta al archivo .mdb o .accdb
        """
        self.db_path = access_db_path
        self.connection_string = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={access_db_path};'
            'ReadOnly=1;'
        )
        self._connection: Optional[pyodbc.Connection] = None
    
    def connect(self) -> bool:
        """Conecta a la base de datos."""
        try:
            self._connection = pyodbc.connect(self.connection_string)
            print(f"✓ Conexión exitosa a: {self.db_path}\n")
            return True
        except pyodbc.Error as e:
            print(f"✗ Error al conectar: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_all_tables(self) -> Dict[str, List[str]]:
        """
        Obtiene todas las tablas y consultas.
        
        Returns:
            Dict con listas de 'tables' y 'queries'
        """
        if not self._connection:
            return {'tables': [], 'queries': []}
        
        cursor = self._connection.cursor()
        
        tables = []
        queries = []
        
        # Obtener todas las tablas
        for table_info in cursor.tables(tableType='TABLE'):
            table_name = table_info.table_name
            # Filtrar tablas del sistema
            if not table_name.startswith('MSys') and not table_name.startswith('~'):
                tables.append(table_name)
        
        # Obtener vistas/consultas (son tipo VIEW)
        for table_info in cursor.tables(tableType='VIEW'):
            query_name = table_info.table_name
            if not query_name.startswith('MSys') and not query_name.startswith('~'):
                queries.append(query_name)
        
        return {
            'tables': sorted(tables),
            'queries': sorted(queries)
        }
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Obtiene la estructura de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Lista de columnas con nombre, tipo, tamaño, nullable
        """
        if not self._connection:
            return []
        
        cursor = self._connection.cursor()
        columns = []
        
        try:
            # Obtener info de columnas
            for column in cursor.columns(table=table_name):
                columns.append({
                    'name': column.column_name,
                    'type': column.type_name,
                    'size': column.column_size,
                    'nullable': column.nullable == 1,
                    'position': column.ordinal_position
                })
        except Exception as e:
            print(f"    ⚠ Error obteniendo estructura: {e}")
        
        return sorted(columns, key=lambda x: x['position'])
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict]:
        """
        Obtiene datos de ejemplo de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            limit: Cantidad de filas a obtener
            
        Returns:
            Lista de diccionarios con los datos
        """
        if not self._connection:
            return []
        
        cursor = self._connection.cursor()
        
        try:
            # Query con TOP para Access
            query = f"SELECT TOP {limit} * FROM [{table_name}]"
            cursor.execute(query)
            
            # Obtener nombres de columnas
            columns = [desc[0] for desc in cursor.description]
            
            # Obtener filas
            rows = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, value in enumerate(row):
                    # Formatear valores
                    if value is None:
                        row_dict[columns[i]] = None
                    elif isinstance(value, (datetime,)):
                        row_dict[columns[i]] = value.strftime('%d/%m/%Y %H:%M')
                    elif isinstance(value, (float, int)):
                        row_dict[columns[i]] = value
                    else:
                        row_dict[columns[i]] = str(value)
                rows.append(row_dict)
            
            return rows
            
        except Exception as e:
            print(f"    ⚠ Error obteniendo datos: {e}")
            return []
    
    def get_record_count(self, table_name: str) -> int:
        """
        Cuenta registros en una tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Cantidad de registros
        """
        if not self._connection:
            return 0
        
        cursor = self._connection.cursor()
        
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            print(f"    ⚠ Error contando registros: {e}")
            return 0
    
    def generate_report(self) -> str:
        """
        Genera un reporte completo de la base de datos.
        
        Returns:
            String con el reporte formateado
        """
        lines = []
        lines.append("=" * 80)
        lines.append("REPORTE DE BASE DE DATOS ACCESS")
        lines.append("=" * 80)
        lines.append(f"Archivo: {self.db_path}")
        lines.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")
        
        # Obtener tablas y consultas
        all_objects = self.get_all_tables()
        tables = all_objects['tables']
        queries = all_objects['queries']
        
        lines.append(f"📊 RESUMEN")
        lines.append(f"   Tablas encontradas: {len(tables)}")
        lines.append(f"   Consultas encontradas: {len(queries)}")
        lines.append("")
        
        # Listar tablas
        if tables:
            lines.append("📁 TABLAS:")
            for table in tables:
                lines.append(f"   - {table}")
            lines.append("")
        
        # Listar consultas
        if queries:
            lines.append("🔍 CONSULTAS/VISTAS:")
            for query in queries:
                lines.append(f"   - {query}")
            lines.append("")
        
        # Detalle de cada tabla
        lines.append("=" * 80)
        lines.append("DETALLE DE TABLAS")
        lines.append("=" * 80)
        lines.append("")
        
        for table in tables:
            self._add_table_detail(lines, table)
        
        # Detalle de cada consulta
        if queries:
            lines.append("=" * 80)
            lines.append("DETALLE DE CONSULTAS/VISTAS")
            lines.append("=" * 80)
            lines.append("")
            
            for query in queries:
                self._add_table_detail(lines, query, is_query=True)
        
        return "\n".join(lines)
    
    def _add_table_detail(self, lines: List[str], table_name: str, is_query: bool = False):
        """Agrega detalle de una tabla al reporte."""
        prefix = "🔍" if is_query else "📋"
        lines.append(f"{prefix} {table_name}")
        lines.append("-" * 80)
        
        # Conteo de registros
        count = self.get_record_count(table_name)
        lines.append(f"   Registros: {count:,}")
        lines.append("")
        
        # Estructura
        structure = self.get_table_structure(table_name)
        if structure:
            lines.append("   ESTRUCTURA:")
            lines.append(f"   {'Campo':<30} {'Tipo':<20} {'Tamaño':<10} {'Nulo'}")
            lines.append(f"   {'-'*30} {'-'*20} {'-'*10} {'-'*5}")
            
            for col in structure:
                nullable = "Sí" if col['nullable'] else "No"
                size = str(col['size']) if col['size'] else "-"
                lines.append(
                    f"   {col['name']:<30} {col['type']:<20} {size:<10} {nullable}"
                )
            lines.append("")
        
        # Datos de ejemplo
        sample_data = self.get_sample_data(table_name, limit=3)
        if sample_data:
            lines.append(f"   DATOS DE EJEMPLO (primeras 3 filas):")
            lines.append("")
            
            for i, row in enumerate(sample_data, 1):
                lines.append(f"   Fila {i}:")
                for key, value in row.items():
                    # Truncar valores largos
                    if value is not None:
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:47] + "..."
                    else:
                        value_str = "NULL"
                    
                    lines.append(f"      {key}: {value_str}")
                lines.append("")
        
        lines.append("")


def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python explore_access.py <ruta_a_access.accdb>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    print("")
    print("╔════════════════════════════════════════╗")
    print("║  Explorador de Base de Datos Access   ║")
    print("╚════════════════════════════════════════╝")
    print("")
    
    explorer = AccessExplorer(db_path)
    
    if not explorer.connect():
        sys.exit(1)
    
    try:
        # Generar reporte
        print("📝 Generando reporte...\n")
        report = explorer.generate_report()
        
        # Mostrar en consola
        print(report)
        
        # Guardar en archivo
        output_file = "access_report.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("")
        print("=" * 80)
        print(f"✓ Reporte guardado en: {output_file}")
        print("=" * 80)
        print("")
        
    finally:
        explorer.disconnect()


if __name__ == '__main__':
    main()
