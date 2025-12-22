"""
Test rápido de conexión a Access.

Uso:
    python test_connection.py "C:\path\to\database.accdb"
"""
import sys
import pyodbc


def test_connection(db_path: str):
    """Prueba rápida de conexión."""
    print("\n" + "="*60)
    print("TEST DE CONEXIÓN A ACCESS")
    print("="*60)
    print(f"\nArchivo: {db_path}")
    
    connection_string = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={db_path};'
        'ReadOnly=1;'
    )
    
    try:
        print("\n→ Intentando conectar...")
        conn = pyodbc.connect(connection_string)
        print("✓ Conexión exitosa")
        
        print("\n→ Obteniendo lista de tablas...")
        cursor = conn.cursor()
        
        tables = []
        for table_info in cursor.tables(tableType='TABLE'):
            name = table_info.table_name
            if not name.startswith('MSys') and not name.startswith('~'):
                tables.append(name)
        
        queries = []
        for table_info in cursor.tables(tableType='VIEW'):
            name = table_info.table_name
            if not name.startswith('MSys') and not name.startswith('~'):
                queries.append(name)
        
        print(f"✓ Encontradas {len(tables)} tablas")
        print(f"✓ Encontradas {len(queries)} consultas/vistas")
        
        if tables:
            print("\nPrimeras 5 tablas:")
            for table in tables[:5]:
                print(f"   - {table}")
        
        if queries:
            print("\nPrimeras 5 consultas:")
            for query in queries[:5]:
                print(f"   - {query}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✓ TEST EXITOSO")
        print("="*60)
        print("\nEjecuta el explorador completo:")
        print(f'   python explore_access.py "{db_path}"')
        print("\nO con PowerShell:")
        print(f'   .\\Explore-Access.ps1 -AccessPath "{db_path}"')
        print("")
        
        return True
        
    except pyodbc.Error as e:
        print(f"\n✗ ERROR DE CONEXIÓN:")
        print(f"   {e}")
        print("\nPosibles soluciones:")
        print("1. Verificar que el archivo existe")
        print("2. Cerrar Access si está abierto")
        print("3. Instalar Microsoft Access Database Engine:")
        print("   https://www.microsoft.com/download/details.aspx?id=54920")
        print("")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUso: python test_connection.py <ruta_access.accdb>")
        print("\nEjemplo:")
        print('   python test_connection.py "C:\\Data\\flota.accdb"')
        print("")
        sys.exit(1)
    
    db_path = sys.argv[1]
    success = test_connection(db_path)
    sys.exit(0 if success else 1)
