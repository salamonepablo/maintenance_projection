"""
Script que prueba múltiples formas de conectar a Access.
Útil cuando no estás seguro de la contraseña o configuración.

Uso:
    python probar_conexiones.py "ruta_al_backend.accdb" "contraseña_opcional"
"""
import sys
import os

try:
    import pyodbc
except ImportError:
    print("✗ pyodbc no instalado. Ejecuta: pip install pyodbc")
    sys.exit(1)


def probar_conexion(ruta, descripcion, connection_string):
    """Prueba una configuración de conexión específica."""
    print(f"\n→ Probando: {descripcion}")
    print(f"   String: {connection_string[:80]}...")
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Contar tablas
        tablas = 0
        for tabla in cursor.tables(tableType='TABLE'):
            if not tabla.table_name.startswith('MSys'):
                tablas += 1
        
        conn.close()
        
        print(f"   ✓ ÉXITO! - {tablas} tablas encontradas")
        return True
        
    except pyodbc.Error as e:
        error_msg = str(e)
        if "contraseña" in error_msg.lower():
            print(f"   ✗ Contraseña incorrecta")
        elif "válida" in error_msg.lower():
            print(f"   ✗ Formato inválido")
        else:
            print(f"   ✗ Error: {error_msg[:60]}")
        return False


def probar_todas_las_opciones(ruta, password=None):
    """Prueba todas las combinaciones posibles."""
    print("="*70)
    print("PROBADOR AUTOMÁTICO DE CONEXIONES ACCESS")
    print("="*70)
    print(f"\nArchivo: {ruta}")
    
    if not os.path.exists(ruta):
        print(f"\n✗ ERROR: El archivo no existe")
        print(f"   {ruta}")
        return False
    
    print("✓ Archivo existe\n")
    
    if password:
        print(f"Contraseña a probar: {password}\n")
    else:
        print("Sin contraseña proporcionada\n")
    
    print("Probando diferentes configuraciones...")
    print("="*70)
    
    base_string = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={ruta};'
    
    # Lista de configuraciones a probar
    configuraciones = []
    
    # 1. Sin contraseña, ReadOnly
    configuraciones.append((
        "Sin contraseña (ReadOnly)",
        base_string + 'ReadOnly=1;'
    ))
    
    # 2. Sin contraseña, sin ReadOnly
    configuraciones.append((
        "Sin contraseña (lectura/escritura)",
        base_string
    ))
    
    if password:
        # 3. Con contraseña en PWD
        configuraciones.append((
            f"Contraseña en PWD ('{password}')",
            base_string + f'PWD={password};ReadOnly=1;'
        ))
        
        # 4. Con contraseña sin ReadOnly
        configuraciones.append((
            f"Contraseña en PWD sin ReadOnly",
            base_string + f'PWD={password};'
        ))
        
        # 5. Con Jet OLEDB (otra forma)
        configuraciones.append((
            f"Jet OLEDB con contraseña",
            f'Provider=Microsoft.ACE.OLEDB.12.0;Data Source={ruta};Jet OLEDB:Database Password={password};'
        ))
    
    # Probar cada configuración
    exito = False
    for desc, conn_str in configuraciones:
        if probar_conexion(ruta, desc, conn_str):
            exito = True
            print("\n" + "="*70)
            print("✓✓✓ CONFIGURACIÓN EXITOSA ENCONTRADA ✓✓✓")
            print("="*70)
            print(f"\nDescripción: {desc}")
            print(f"\nConnection String exitoso:")
            print(f"{conn_str}\n")
            break
    
    if not exito:
        print("\n" + "="*70)
        print("✗ NINGUNA CONFIGURACIÓN FUNCIONÓ")
        print("="*70)
        print("\nPosibles causas:")
        print("1. La contraseña es diferente")
        print("2. El archivo está abierto por otro usuario")
        print("3. No tienes permisos de acceso")
        print("4. El archivo está corrupto")
        print("\nSugerencias:")
        print("- Cierra Access si está abierto")
        print("- Verifica que puedas abrir el archivo manualmente")
        print("- Pregunta a quien administra la base de datos")
        print()
    
    return exito


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUso:")
        print('  python probar_conexiones.py "C:\\ruta\\backend.accdb"')
        print('  python probar_conexiones.py "C:\\ruta\\backend.accdb" "contraseña"\n')
        print("Ejemplos:")
        print('  python probar_conexiones.py "G:\\BD\\datos.accdb"')
        print('  python probar_conexiones.py "G:\\BD\\datos.accdb" "0733"\n')
        sys.exit(1)
    
    ruta = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    exito = probar_todas_las_opciones(ruta, password)
    sys.exit(0 if exito else 1)
