"""
Ver datos de ejemplo de las tablas candidatas para sincronización.
"""
import pyodbc
from datetime import datetime

# backend_path = r'G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb'
backend_path = r'C:\Users\pablo.salamone\Documents\BBDD\DB_CCEE_Programación 1.1.accdb'
#password = '0733'
password =''

connection_string = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={backend_path};'
    f'PWD={password};'
    'ReadOnly=1;'
)

def mostrar_tabla(cursor, nombre_tabla, filtro=None, limit=5):
    """Muestra datos de una tabla."""
    print("\n" + "="*80)
    print(f"📋 TABLA: {nombre_tabla}")
    print("="*80)
    
    try:
        query = f"SELECT TOP {limit} * FROM [{nombre_tabla}]"
        if filtro:
            query = f"SELECT TOP {limit} * FROM [{nombre_tabla}] WHERE {filtro}"
        
        cursor.execute(query)
        
        # Nombres de columnas
        columnas = [desc[0] for desc in cursor.description]
        print(f"\nColumnas: {', '.join(columnas)}\n")
        
        # Datos
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"Fila {i}:")
            for col, val in zip(columnas, row):
                if isinstance(val, datetime):
                    val = val.strftime('%d/%m/%Y %H:%M')
                print(f"  {col}: {val}")
            print()
        
        # Contar total
        cursor.execute(f"SELECT COUNT(*) FROM [{nombre_tabla}]")
        total = cursor.fetchone()[0]
        print(f"Total de registros: {total:,}")
        
    except Exception as e:
        print(f"⚠ Error: {e}")

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    print("="*80)
    print("DATOS DE EJEMPLO - TABLAS CANDIDATAS")
    print("="*80)
    
    # 1. Módulos CSR
    mostrar_tabla(cursor, "A_00_Módulos", "Módulos LIKE 'M%'", limit=5)
    
    # 2. Lecturas de Kilometraje
    mostrar_tabla(cursor, "A_00_Kilometrajes", "Módulo LIKE 'M%'", limit=5)
    
    # 3. Eventos - Opción 1
    mostrar_tabla(cursor, "A_00_OT_Simaf", "Módulo LIKE 'M%'", limit=5)
        
    # 4. Ver tipos de tareas en A_00_OT_Simaf
    print("\n" + "="*80)
    print("🔍 TIPOS DE TAREAS EN A_00_OT_Simaf (CSR)")
    print("="*80)
    cursor.execute("""
        SELECT DISTINCT Tarea, COUNT(*) as Total
        FROM [A_00_OT_Simaf]
        WHERE Módulo LIKE 'M%'
        GROUP BY Tarea
        ORDER BY COUNT(*) DESC
    """)
    print("\nTarea | Total de eventos")
    print("-" * 40)
    for row in cursor.fetchall():
        print(f"{row[0]:<30} | {row[1]:>6}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✓ Análisis completado")
    print("="*80)
    
except Exception as e:
    print(f"✗ Error: {e}")
