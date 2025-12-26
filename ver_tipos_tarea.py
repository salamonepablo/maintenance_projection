"""
Ver tipos de Tarea en A_00_OT_Simaf para módulos CSR.
"""
import pyodbc

backend_path = r'C:\Users\pablo.salamone\Documents\BBDD\DB_CCEE_Programación 1.1.accdb'
password = ''

connection_string = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={backend_path};'
    f'PWD={password};'
    'ReadOnly=1;'
)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    print("="*80)
    print("TIPOS DE TAREAS CSR EN A_00_OT_Simaf")
    print("="*80)
    print()
    
    # Contar por Tarea
    #WHERE Módulo LIKE 'M%'
    cursor.execute("""
        SELECT Tarea, COUNT(*) as Total
        FROM A_00_OT_Simaf
        WHERE Módulo >= 01 AND Módulo <= 86
        GROUP BY Tarea
        ORDER BY COUNT(*) DESC
    """)
    
    print("Tarea         | Total eventos")
    print("-" * 40)
    
    tareas = []
    for row in cursor.fetchall():
        tarea = row[0] if row[0] else "(vacío)"
        total = row[1]
        print(f"{tarea:<13} | {total:>6,}")
        tareas.append(tarea)
    
    print()
    print("="*80)
    print(f"Total de tipos diferentes: {len(tareas)}")
    print("="*80)
    
    # Mostrar ejemplos de eventos CSR
    print()
    print("EJEMPLOS DE EVENTOS CSR:")
    print("="*80)
    
    #WHERE Módulo LIKE 'M%'
    cursor.execute("""
        SELECT TOP 10 Módulo, Tarea, Km, Fecha_Fin
        FROM A_00_OT_Simaf
        WHERE Módulo >= 01 AND Módulo <= 86
        ORDER BY Fecha_Fin DESC
    """)
    
    for row in cursor.fetchall():
        modulo = row[0]
        tarea = row[1]
        km = row[2]
        fecha = row[3].strftime('%d/%m/%Y') if row[3] else 'N/A'
        print(f"{modulo} - {tarea:<10} @ {km:>10,} km - {fecha}")
    
    conn.close()
    print()
    print("="*80)
    print("✓ Completado")
    print("="*80)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
