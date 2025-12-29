"""
Verifica qué módulo corresponde al Id_Módulos = 39
"""
import pyodbc

backend_path = r'C:\Users\pablo\Documents\BBDD\DB_CCEE_Programación 1.1.accdb'
password = ''

connection_string = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={backend_path};'
    f'PWD={password};'
    'ReadOnly=1;'
)

print("="*80)
print("VERIFICACIÓN: Id_Módulos = 39")
print("="*80)
print()

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Consulta directa a A_00_Módulos
    print("1️⃣ Consulta directa en A_00_Módulos:")
    print("-" * 80)
    cursor.execute("""
        SELECT Id_Módulos, Módulos, Clase_Vehículos
        FROM A_00_Módulos
        WHERE Id_Módulos = 39
    """)
    
    row = cursor.fetchone()
    if row:
        print(f"   Id_Módulos:      {row[0]}")
        print(f"   Módulos:         {row[1]}")
        print(f"   Clase_Vehículos: {row[2]}")
    else:
        print("   ⚠ No se encontró el Id_Módulos = 39")
    
    print()
    
    # Ver contexto (registros alrededor)
    print("2️⃣ Módulos cercanos (35-45):")
    print("-" * 80)
    cursor.execute("""
        SELECT Id_Módulos, Módulos, Clase_Vehículos
        FROM A_00_Módulos
        WHERE Id_Módulos BETWEEN 35 AND 45
        ORDER BY Id_Módulos
    """)
    
    print(f"   {'ID':<5} | {'Módulo':<8} | {'Clase'}")
    print("   " + "-" * 40)
    for row in cursor.fetchall():
        print(f"   {row[0]:<5} | {row[1]:<8} | {row[2]}")
    
    print()
    
    # Verificar si tiene eventos
    print("3️⃣ Eventos del módulo Id_Módulos = 39:")
    print("-" * 80)
    cursor.execute("""
        SELECT COUNT(*) as Total
        FROM A_00_OT_Simaf
        WHERE Módulo LIKE '*M12*'
    """)
    
    count = cursor.fetchone()[0]
    print(f"   Total de eventos: {count}")
    
    if count > 0:
        print()
        print("   Últimos 5 eventos:")
        cursor.execute("""
            SELECT TOP 5 Módulo, Tarea, Km, Fecha_Fin
            FROM A_00_OT_Simaf
            WHERE Módulo LIKE '*M12*'
            ORDER BY Fecha_Fin DESC
        """)
        
        print(f"   {'Módulo':<8} | {'Tarea':<10} | {'Km':<12} | {'Fecha'}")
        print("   " + "-" * 60)
        for row in cursor.fetchall():
            print(f"   {row[0]:<8} | {row[1]:<10} | {row[2]:<12} | {row[3]}")
    
    print()
    
    # Verificar con JOIN (como en el código real)
    print("4️⃣ JOIN directo por texto (corrección):")
    print("-" * 80)
    
    # Primero ver qué tiene realmente el campo Módulo en OT_Simaf
    cursor.execute("""
        SELECT TOP 5
            Módulo,
            TypeName(Módulo) AS Tipo_Dato
        FROM A_00_OT_Simaf
        ORDER BY Módulo
    """)
    
    print("   Ejemplos de A_00_OT_Simaf.Módulo:")
    print(f"   {'Valor':<10} | {'Tipo'}")
    print("   " + "-" * 40)
    for row in cursor.fetchall():
        print(f"   {row[0]:<10} | {row[1]}")
    
    print()
    
    # JOIN directo (asumiendo que es texto)
    cursor.execute("""
        SELECT 
            ot.Módulo AS OT_Modulo,
            m.Módulos AS M_Modulos,
            m.Id_Módulos AS M_Id,
            m.Clase_Vehículos,
            COUNT(*) AS Total_Eventos
        FROM A_00_OT_Simaf AS ot
        INNER JOIN A_00_Módulos AS m ON ot.Módulo = m.Id_Módulos
        WHERE m.Id_Módulos = 39
        GROUP BY ot.Módulo, m.Módulos, m.Id_Módulos, m.Clase_Vehículos
    """)
    
    row = cursor.fetchone()
    if row:
        print("   JOIN directo: ot.Módulo = m.Id_Módulos")
        print(f"   ot.Módulo:          {row[0]}")
        print(f"   m.Módulos:          {row[1]}")
        print(f"   m.Id_Módulos:       {row[2]}")
        print(f"   m.Clase_Vehículos:  {row[3]}")
        print(f"   Total eventos:      {row[4]}")
        print()
        
        if row[3] == 'C' or row[3] == 3:
            print("   ✅ Es un módulo CSR - Será incluido en la sincronización")
        elif row[3] == 'B':
            print("   ⚠️  Es un módulo Toshiba - Será EXCLUIDO de la sincronización")
        else:
            print(f"   ❓ Clase: {row[3]}")
    else:
        print("   ⚠ No se pudo hacer el JOIN directo")
    
    conn.close()
    
    print()
    print("="*80)
    print("✓ Verificación completada")
    print("="*80)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
