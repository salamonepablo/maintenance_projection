"""
Script para listar todas las tablas disponibles en el backend Access.

Uso:
    python listar_tablas_backend.py
"""
import pyodbc

# Configuración del backend
backend_path = r'G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb'
password = '0733'

connection_string = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={backend_path};'
    f'PWD={password};'
    'ReadOnly=1;'
)

print("="*80)
print("TABLAS EN EL BACKEND ACCESS")
print("="*80)
print()

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Listar todas las tablas
    tablas = []
    for table_info in cursor.tables(tableType='TABLE'):
        nombre = table_info.table_name
        if not nombre.startswith('MSys') and not nombre.startswith('~'):
            tablas.append(nombre)
    
    tablas.sort()
    
    print(f"✓ Conexión exitosa al backend")
    print(f"✓ {len(tablas)} tablas encontradas\n")
    print("="*80)
    
    for i, tabla in enumerate(tablas, 1):
        print(f"{i:3}. {tabla}")
        
        # Ver campos de cada tabla
        try:
            cursor.execute(f"SELECT TOP 1 * FROM [{tabla}]")
            if cursor.description:
                campos = [desc[0] for desc in cursor.description]
                print(f"     Campos: {', '.join(campos[:5])}")
                if len(campos) > 5:
                    print(f"            ... y {len(campos) - 5} más")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
            count = cursor.fetchone()[0]
            print(f"     Registros: {count:,}")
            
        except Exception as e:
            print(f"     ⚠ Error: {str(e)[:50]}")
        
        print()
    
    print("="*80)
    
    # Buscar tablas específicas
    print("\n🔍 BUSCANDO TABLAS CLAVE:\n")
    
    keywords = ['Kilometr', 'OT', 'Manten', 'Simaf', 'Modulo', 'Km']
    for keyword in keywords:
        matches = [t for t in tablas if keyword.lower() in t.lower()]
        if matches:
            print(f"  '{keyword}': {', '.join(matches)}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✓ Listado completado")
    print("="*80)
    
except pyodbc.Error as e:
    print(f"✗ Error de conexión: {e}")

except Exception as e:
    print(f"✗ Error: {e}")
