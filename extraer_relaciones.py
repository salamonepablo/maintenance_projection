"""
Extrae todas las relaciones (foreign keys) de una base Access.
"""
import os
import pyodbc

password = os.getenv('ACCESS_PASSWORD')
backend_path = r'C:\Users\pablo\Documents\BBDD\DB_CCEE_Programación 1.1.accdb'
    

connection_string = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={backend_path};'
    f'PWD={password};'
    'ReadOnly=1;'
)

print("="*80)
print("RELACIONES DE LA BASE DE DATOS ACCESS")
print("="*80)
print()

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Obtener información de relaciones
    relations = {}
    
    # Obtener todas las tablas
    tables = []
    for table_info in cursor.tables(tableType='TABLE'):
        nombre = table_info.table_name
        if not nombre.startswith('MSys') and not nombre.startswith('~'):
            tables.append(nombre)
    
    print(f"Analizando {len(tables)} tablas...\n")
    
    # Para cada tabla, obtener sus foreign keys
    for table in sorted(tables):
        try:
            fks = cursor.foreignKeys(table=table)
            table_fks = []
            
            for fk in fks:
                fk_info = {
                    'fk_table': fk.fktable_name,
                    'fk_column': fk.fkcolumn_name,
                    'pk_table': fk.pktable_name,
                    'pk_column': fk.pkcolumn_name,
                }
                table_fks.append(fk_info)
            
            if table_fks:
                relations[table] = table_fks
        except:
            pass
    
    # Mostrar relaciones encontradas
    if relations:
        print("RELACIONES ENCONTRADAS:")
        print("="*80)
        
        for table, fks in sorted(relations.items()):
            print(f"\n📋 {table}")
            for fk in fks:
                print(f"   └─ {fk['fk_column']} → {fk['pk_table']}.{fk['pk_column']}")
    else:
        print("⚠ No se encontraron relaciones mediante foreignKeys()")
        print()
        print("PLAN B: Analizar tablas manualmente")
        print("="*80)
        
        # Analizar A_00_OT_Simaf específicamente
        print("\n📋 A_00_OT_Simaf:")
        cursor.execute("SELECT TOP 1 * FROM A_00_OT_Simaf")
        columnas_ot = [desc[0] for desc in cursor.description]
        print(f"   Columnas: {', '.join(columnas_ot)}")
        
        # Analizar A_00_Módulos
        print("\n📋 A_00_Módulos:")
        cursor.execute("SELECT TOP 5 Id_Módulos, Módulos, Clase_Vehículos FROM A_00_Módulos ORDER BY Id_Módulos")
        print("   Id_Módulos | Módulos | Clase_Vehículos")
        print("   " + "-"*40)
        for row in cursor.fetchall():
            print(f"   {row[0]:<10} | {row[1]:<7} | {row[2]}")
        
        # Verificar si A_00_OT_Simaf.Módulo es FK a Id_Módulos
        print("\n🔍 Verificando relación A_00_OT_Simaf.Módulo → A_00_Módulos.Id_Módulos:")
        cursor.execute("""
            SELECT TOP 5
                ot.Módulo AS FK_Value,
                m.Id_Módulos AS PK_Value,
                m.Módulos AS Modulo_Nombre,
                m.Clase_Vehículos
            FROM A_00_OT_Simaf AS ot
            INNER JOIN A_00_Módulos AS m ON ot.Módulo = m.Id_Módulos
            ORDER BY ot.Módulo
        """)
        
        print("   FK → PK | Módulo  | Clase")
        print("   " + "-"*40)
        for row in cursor.fetchall():
            print(f"   {row[0]:>2} → {row[1]:<2} | {row[2]:<7} | {row[3]}")
        
        print("\n   ✓ JOIN funciona: A_00_OT_Simaf.Módulo = A_00_Módulos.Id_Módulos")
        
        # Lo mismo para A_00_Kilometrajes
        print("\n🔍 Verificando relación A_00_Kilometrajes.Módulo → A_00_Módulos.Id_Módulos:")
        cursor.execute("""
            SELECT TOP 5
                k.Módulo AS FK_Value,
                m.Id_Módulos AS PK_Value,
                m.Módulos AS Modulo_Nombre,
                m.Clase_Vehículos
            FROM A_00_Kilometrajes AS k
            INNER JOIN A_00_Módulos AS m ON k.Módulo = m.Id_Módulos
            ORDER BY k.Módulo
        """)
        
        print("   FK → PK | Módulo  | Clase")
        print("   " + "-"*40)
        for row in cursor.fetchall():
            print(f"   {row[0]:>2} → {row[1]:<2} | {row[2]:<7} | {row[3]}")
        
        print("\n   ✓ JOIN funciona: A_00_Kilometrajes.Módulo = A_00_Módulos.Id_Módulos")
    
    conn.close()
    
    print("\n" + "="*80)
    print("CONCLUSIÓN:")
    print("="*80)
    print("Usar en queries:")
    print("  FROM A_00_OT_Simaf AS ot")
    print("  INNER JOIN A_00_Módulos AS m ON ot.Módulo = m.Id_Módulos")
    print("  WHERE m.Clase_Vehículos = 'C'")
    print()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
