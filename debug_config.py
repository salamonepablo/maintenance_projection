"""
Script de debug para verificar configuración de Access.

Muestra:
- Qué está leyendo del .env
- Si el archivo existe
- Si puede conectar
"""
import os
from pathlib import Path

print("="*80)
print("DEBUG - CONFIGURACIÓN ACCESS")
print("="*80)
print()

# 1. Verificar si .env existe
env_path = Path(".env")
print(f"1. Archivo .env existe: {env_path.exists()}")
if env_path.exists():
    print(f"   Ubicación: {env_path.absolute()}")
print()

# 2. Intentar leer con decouple
try:
    from decouple import config
    
    password = config('ACCESS_DB_PASSWORD')
    db_path = config('ACCESS_DB_PATH')
    
    print("2. Configuración leída con decouple:")
    print(f"   ACCESS_DB_PASSWORD: '{password}'")
    print(f"   Longitud: {len(password)} caracteres")
    print(f"   Tipo: {type(password)}")
    print(f"   Bytes: {password.encode('utf-8')}")
    print()
    print(f"   ACCESS_DB_PATH: {db_path}")
    print()
    
except Exception as e:
    print(f"   ✗ Error leyendo .env: {e}")
    print()

# 3. Verificar si el archivo Access existe
print("3. Verificación del archivo Access:")
try:
    from decouple import config
    db_path = config('ACCESS_DB_PATH')
    access_file = Path(db_path)
    print(f"   Archivo existe: {access_file.exists()}")
    if access_file.exists():
        print(f"   Tamaño: {access_file.stat().st_size:,} bytes")
except Exception as e:
    print(f"   ✗ Error: {e}")
print()

# 4. Probar conexión con diferentes formatos de contraseña
print("4. Probando conexión con la contraseña leída:")
print()

try:
    import pyodbc
    from decouple import config
    
    db_path = config('ACCESS_DB_PATH')
    password = config('ACCESS_DB_PASSWORD')
    
    # Probar sin contraseña primero
    print("   a) Intentando SIN contraseña...")
    try:
        conn_str_no_pwd = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={db_path};'
            'ReadOnly=1;'
        )
        conn = pyodbc.connect(conn_str_no_pwd)
        print("      ✓ ÉXITO - El archivo NO tiene contraseña!")
        conn.close()
    except pyodbc.Error as e:
        print(f"      ✗ Fallo: {str(e)[:60]}...")
    print()
    
    # Probar con contraseña tal cual
    print(f"   b) Intentando con contraseña: '{password}'")
    try:
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={db_path};'
            f'PWD={password};'
            'ReadOnly=1;'
        )
        conn = pyodbc.connect(conn_str)
        print("      ✓ ÉXITO - Conexión establecida!")
        
        # Ver qué hay
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT Módulo) FROM A_00_Kilometrajes WHERE Módulo LIKE 'M%'")
        count = cursor.fetchone()[0]
        print(f"      Módulos CSR encontrados: {count}")
        
        conn.close()
    except pyodbc.Error as e:
        print(f"      ✗ Fallo: {str(e)[:100]}")
    print()
    
    # Probar con contraseña .strip() (por si tiene espacios)
    print(f"   c) Intentando con contraseña.strip(): '{password.strip()}'")
    try:
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={db_path};'
            f'PWD={password.strip()};'
            'ReadOnly=1;'
        )
        conn = pyodbc.connect(conn_str)
        print("      ✓ ÉXITO - ¡La contraseña tenía espacios!")
        conn.close()
    except pyodbc.Error as e:
        print(f"      ✗ Fallo: {str(e)[:60]}...")
    print()
    
except Exception as e:
    print(f"   ✗ Error general: {e}")
    import traceback
    traceback.print_exc()

print("="*80)
print("FIN DEBUG")
print("="*80)
