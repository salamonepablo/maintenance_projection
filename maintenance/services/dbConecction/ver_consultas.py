"""
Explorador de CONSULTAS y VISTAS de Access.

Este script lista todas las consultas guardadas (queries) en Access,
que son diferentes de las tablas y suelen ser las que se usan realmente.

Uso:
    python ver_consultas.py
"""
import pyodbc


def ver_consultas():
    """Lista todas las consultas de Access."""
    
    # Configuración que sabemos que funciona
    ruta = r'G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb'
    password = '0733'
    
    connection_string = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={ruta};'
        f'PWD={password};'
        'ReadOnly=1;'
    )
    
    print("="*80)
    print("CONSULTAS (QUERIES) EN ACCESS")
    print("="*80)
    print()
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Obtener consultas (tipo VIEW)
        print("→ Buscando consultas guardadas...\n")
        
        consultas = []
        for table_info in cursor.tables(tableType='VIEW'):
            nombre = table_info.table_name
            if not nombre.startswith('MSys') and not nombre.startswith('~'):
                consultas.append(nombre)
        
        # Ordenar
        consultas.sort()
        
        if consultas:
            print(f"✓ {len(consultas)} consultas encontradas:\n")
            print("="*80)
            
            for i, consulta in enumerate(consultas, 1):
                print(f"{i:3}. {consulta}")
                
                # Ver estructura de la consulta
                try:
                    # Ejecutar para ver columnas
                    cursor.execute(f"SELECT TOP 1 * FROM [{consulta}]")
                    
                    if cursor.description:
                        columnas = [desc[0] for desc in cursor.description]
                        print(f"     Campos: {', '.join(columnas[:8])}")
                        if len(columnas) > 8:
                            print(f"            ... y {len(columnas) - 8} más")
                    
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM [{consulta}]")
                    count = cursor.fetchone()[0]
                    print(f"     Registros: {count:,}")
                    
                except Exception as e:
                    print(f"     ⚠ Error: {str(e)[:50]}")
                
                print()
        
        else:
            print("No se encontraron consultas guardadas.")
        
        print("="*80)
        
        # También listar tablas para comparar
        print("\nTABLAS (para comparar):\n")
        print("="*80)
        
        tablas = []
        for table_info in cursor.tables(tableType='TABLE'):
            nombre = table_info.table_name
            if not nombre.startswith('MSys') and not nombre.startswith('~'):
                tablas.append(nombre)
        
        tablas.sort()
        
        for i, tabla in enumerate(tablas, 1):
            print(f"{i:3}. {tabla}")
        
        print()
        print("="*80)
        print(f"\nRESUMEN:")
        print(f"  Consultas (queries): {len(consultas)}")
        print(f"  Tablas: {len(tablas)}")
        print(f"  Total: {len(consultas) + len(tablas)}")
        print()
        
        conn.close()
        
        # Guardar en archivo
        output = "lista_consultas.txt"
        with open(output, 'w', encoding='utf-8') as f:
            f.write("CONSULTAS ENCONTRADAS\n")
            f.write("="*80 + "\n\n")
            for consulta in consultas:
                f.write(f"- {consulta}\n")
            f.write("\n" + "="*80 + "\n")
            f.write("TABLAS ENCONTRADAS\n")
            f.write("="*80 + "\n\n")
            for tabla in tablas:
                f.write(f"- {tabla}\n")
        
        print(f"✓ Lista guardada en: {output}")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == '__main__':
    ver_consultas()
