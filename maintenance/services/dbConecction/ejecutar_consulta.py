"""
Ejecutor de consultas personalizadas en Access.

Permite ejecutar cualquier consulta SQL o ver datos de consultas guardadas.

Uso:
    python ejecutar_consulta.py "nombre_consulta"
    python ejecutar_consulta.py "SELECT * FROM tabla WHERE ..."
"""
import sys
import pyodbc
from datetime import datetime


def ejecutar_consulta(consulta_o_nombre, limit=10):
    """Ejecuta una consulta y muestra resultados."""
    
    # Configuración
    ruta = r'G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb'
    password = '0733'
    
    connection_string = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={ruta};'
        f'PWD={password};'
        'ReadOnly=1;'
    )
    
    print("="*80)
    print("EJECUTOR DE CONSULTAS ACCESS")
    print("="*80)
    print()
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Determinar si es nombre de consulta o SQL
        es_sql = 'SELECT' in consulta_o_nombre.upper() or 'FROM' in consulta_o_nombre.upper()
        
        if es_sql:
            print(f"→ Ejecutando SQL personalizado...")
            print(f"   {consulta_o_nombre[:60]}...")
            print()
            sql = consulta_o_nombre
        else:
            print(f"→ Ejecutando consulta guardada: {consulta_o_nombre}")
            print()
            sql = f"SELECT TOP {limit} * FROM [{consulta_o_nombre}]"
        
        # Ejecutar
        cursor.execute(sql)
        
        # Obtener columnas
        if not cursor.description:
            print("✓ Consulta ejecutada (sin resultados)")
            conn.close()
            return
        
        columnas = [desc[0] for desc in cursor.description]
        
        print(f"✓ {len(columnas)} columnas encontradas:")
        print()
        
        # Mostrar nombres de columnas
        header = " | ".join([f"{col[:20]:<20}" for col in columnas])
        print(header)
        print("-" * len(header))
        
        # Obtener y mostrar filas
        filas = cursor.fetchall()
        
        if not filas:
            print("(Sin registros)")
        else:
            for i, fila in enumerate(filas, 1):
                valores = []
                for valor in fila:
                    if valor is None:
                        valores.append("NULL".ljust(20))
                    elif isinstance(valor, datetime):
                        valores.append(valor.strftime('%d/%m/%Y %H:%M')[:20].ljust(20))
                    elif isinstance(valor, (int, float)):
                        valores.append(str(valor)[:20].ljust(20))
                    else:
                        valores.append(str(valor)[:20].ljust(20))
                
                print(" | ".join(valores))
                
                if i >= limit and not es_sql:
                    print()
                    print(f"... (mostrando primeras {limit} filas)")
                    break
        
        print()
        print("="*80)
        print(f"Total de filas mostradas: {min(len(filas), limit)}")
        
        # Contar total si es consulta guardada
        if not es_sql:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{consulta_o_nombre}]")
                total = cursor.fetchone()[0]
                print(f"Total de registros en la consulta: {total:,}")
            except:
                pass
        
        print("="*80)
        print()
        
        # Guardar en archivo
        output = f"resultado_consulta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output, 'w', encoding='utf-8') as f:
            f.write("RESULTADO DE CONSULTA\n")
            f.write("="*80 + "\n\n")
            f.write(f"Consulta: {consulta_o_nombre}\n")
            f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write("Columnas:\n")
            for col in columnas:
                f.write(f"  - {col}\n")
            f.write(f"\nRegistros (primeros {limit}):\n\n")
            
            for fila in filas[:limit]:
                f.write("\n")
                for col, val in zip(columnas, fila):
                    if val is None:
                        val_str = "NULL"
                    elif isinstance(val, datetime):
                        val_str = val.strftime('%d/%m/%Y %H:%M')
                    else:
                        val_str = str(val)
                    f.write(f"  {col}: {val_str}\n")
        
        print(f"✓ Resultado guardado en: {output}")
        print()
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print()


def mostrar_ayuda():
    """Muestra ayuda de uso."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          EJECUTOR DE CONSULTAS ACCESS                        ║
╚══════════════════════════════════════════════════════════════╝

USO:

1. Ver datos de una consulta guardada:
   python ejecutar_consulta.py "nombre_consulta"
   
   Ejemplo:
   python ejecutar_consulta.py "qry_MantenimientosCSR"

2. Ejecutar SQL personalizado:
   python ejecutar_consulta.py "SELECT * FROM tabla WHERE campo = valor"
   
   Ejemplo:
   python ejecutar_consulta.py "SELECT Modulo, Fecha FROM TblGeneral WHERE Modulo = 'M01'"

3. Listar todas las consultas disponibles:
   python ver_consultas.py

══════════════════════════════════════════════════════════════

EJEMPLOS DE CONSULTAS ÚTILES:

# Ver módulos CSR
python ejecutar_consulta.py "SELECT * FROM [02_Módulos] WHERE Módulo LIKE 'M%'"

# Ver últimos mantenimientos
python ejecutar_consulta.py "SELECT TOP 20 * FROM TblGeneral ORDER BY Fecha DESC"

# Ver lecturas de km de un módulo
python ejecutar_consulta.py "SELECT * FROM [32_Lubricación_Pestaña] WHERE Módulo = 1"

# Contar registros por tipo de trabajo
python ejecutar_consulta.py "SELECT TipoTrabajo, COUNT(*) as Total FROM [08_HorasHombre] GROUP BY TipoTrabajo"

══════════════════════════════════════════════════════════════
""")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        mostrar_ayuda()
        sys.exit(1)
    
    consulta = sys.argv[1]
    
    if consulta.lower() in ['help', '--help', '-h', '?']:
        mostrar_ayuda()
    else:
        ejecutar_consulta(consulta)
