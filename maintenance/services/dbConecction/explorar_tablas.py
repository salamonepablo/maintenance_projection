"""
Explorador de estructura Access - Con configuración exitosa.

Este script usa la configuración de conexión que YA SABEMOS que funciona.
Explora las 30 tablas y genera un reporte completo.

Uso:
    python explorar_tablas.py
"""
import pyodbc
from datetime import datetime


def explorar_base():
    """Explora la base de datos con la configuración exitosa."""
    
    # Configuración que SABEMOS que funciona
    ruta = r'G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb'
    password = '0733'
    
    connection_string = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={ruta};'
        f'PWD={password};'
        'ReadOnly=1;'
    )
    
    print("="*80)
    print("EXPLORADOR DE ESTRUCTURA - BASE CCEE MANTENIMIENTO")
    print("="*80)
    print(f"\nConectando...")
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("✓ Conectado exitosamente\n")
        
        # Obtener todas las tablas
        print("→ Obteniendo lista de tablas...\n")
        tablas = []
        for tabla_info in cursor.tables(tableType='TABLE'):
            nombre = tabla_info.table_name
            if not nombre.startswith('MSys') and not nombre.startswith('~'):
                tablas.append(nombre)
        
        tablas.sort()
        
        print(f"✓ {len(tablas)} tablas encontradas\n")
        print("="*80)
        print("LISTA DE TABLAS")
        print("="*80)
        
        for i, tabla in enumerate(tablas, 1):
            print(f"{i:2}. {tabla}")
        
        print("\n" + "="*80)
        print("ESTRUCTURA DETALLADA DE CADA TABLA")
        print("="*80)
        
        reporte = []
        reporte.append("="*80)
        reporte.append("REPORTE DE ESTRUCTURA - BASE CCEE MANTENIMIENTO")
        reporte.append("="*80)
        reporte.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        reporte.append(f"Tablas: {len(tablas)}")
        reporte.append("="*80)
        reporte.append("")
        
        # Explorar cada tabla
        for tabla in tablas:
            print(f"\n{'='*80}")
            print(f"📋 {tabla}")
            print('='*80)
            
            reporte.append("="*80)
            reporte.append(f"📋 {tabla}")
            reporte.append("="*80)
            
            # Contar registros
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
                count = cursor.fetchone()[0]
                print(f"Registros: {count:,}")
                reporte.append(f"Registros: {count:,}")
            except:
                print("Registros: Error al contar")
                reporte.append("Registros: Error al contar")
            
            print()
            reporte.append("")
            
            # Estructura
            print("ESTRUCTURA:")
            print(f"{'Campo':<35} {'Tipo':<20} {'Tamaño':<10} {'Nulo'}")
            print(f"{'-'*35} {'-'*20} {'-'*10} {'-'*5}")
            
            reporte.append("ESTRUCTURA:")
            reporte.append(f"{'Campo':<35} {'Tipo':<20} {'Tamaño':<10} {'Nulo'}")
            reporte.append(f"{'-'*35} {'-'*20} {'-'*10} {'-'*5}")
            
            columnas = []
            try:
                for col in cursor.columns(table=tabla):
                    columnas.append({
                        'name': col.column_name,
                        'type': col.type_name,
                        'size': col.column_size,
                        'nullable': col.nullable == 1,
                        'position': col.ordinal_position
                    })
            except:
                print("Error obteniendo estructura")
                reporte.append("Error obteniendo estructura")
            
            columnas.sort(key=lambda x: x['position'])
            
            for col in columnas:
                nullable = "Sí" if col['nullable'] else "No"
                size = str(col['size']) if col['size'] else "-"
                linea = f"{col['name']:<35} {col['type']:<20} {size:<10} {nullable}"
                print(linea)
                reporte.append(linea)
            
            print()
            reporte.append("")
            
            # Datos de ejemplo (primeras 3 filas)
            print("DATOS DE EJEMPLO (primeras 3 filas):")
            reporte.append("DATOS DE EJEMPLO (primeras 3 filas):")
            
            try:
                cursor.execute(f"SELECT TOP 3 * FROM [{tabla}]")
                rows = cursor.fetchall()
                
                if cursor.description:
                    col_names = [desc[0] for desc in cursor.description]
                    
                    for row_num, row in enumerate(rows, 1):
                        print(f"\nFila {row_num}:")
                        reporte.append(f"\nFila {row_num}:")
                        
                        for col_name, value in zip(col_names, row):
                            # Formatear valor
                            if value is None:
                                val_str = "NULL"
                            elif isinstance(value, datetime):
                                val_str = value.strftime('%d/%m/%Y %H:%M')
                            elif isinstance(value, (int, float)):
                                val_str = str(value)
                            else:
                                val_str = str(value)
                                if len(val_str) > 60:
                                    val_str = val_str[:57] + "..."
                            
                            linea = f"   {col_name}: {val_str}"
                            print(linea)
                            reporte.append(linea)
                
            except Exception as e:
                error_msg = f"Error obteniendo datos: {str(e)[:50]}"
                print(error_msg)
                reporte.append(error_msg)
            
            print()
            reporte.append("")
            reporte.append("")
        
        conn.close()
        
        # Guardar reporte
        output_file = "reporte_ccee_completo.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(reporte))
        
        print("\n" + "="*80)
        print(f"✓ REPORTE COMPLETO GUARDADO EN: {output_file}")
        print("="*80)
        print()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


if __name__ == '__main__':
    print()
    explorar_base()
