# 🔍 Kit de Exploración Access - Quick Start

Kit para explorar tu base Access real y generar reporte completo de estructura.

## 📦 Contenido

- **test_connection.py** - Test rápido de conexión (30 seg)
- **Test-Connection.ps1** - Wrapper PowerShell para test
- **explore_access.py** (11 KB) - Explorador completo
- **Explore-Access.ps1** (6.5 KB) - Wrapper PowerShell con verificaciones
- **GUIA_EXPLORACION.md** (6.8 KB) - Guía completa paso a paso

## ⚡ Quick Start (4 pasos)

### Paso 0: Test Rápido (Opcional pero recomendado)

```powershell
# Probar conexión primero (30 segundos)
.\Test-Connection.ps1 -AccessPath "C:\Ruta\A\Tu\Base.accdb"
```

Si funciona, continúa con exploración completa ⬇

### Pasos Completos

```powershell
# 1. Instalar pyodbc
pip install pyodbc

# 2. Explorar Access (reemplaza con tu ruta)
.\Explore-Access.ps1 -AccessPath "C:\Ruta\A\Tu\Base.accdb"

# 3. Revisar reporte generado
notepad access_report.txt
```

## 📊 Qué Hace

1. ✅ Conecta a Access (solo lectura)
2. ✅ Lista TODAS las tablas y consultas
3. ✅ Muestra estructura de cada una (campos, tipos)
4. ✅ Muestra datos de ejemplo (3 filas)
5. ✅ Cuenta registros
6. ✅ Genera reporte detallado en TXT

## 🎯 Resultado

Archivo `access_report.txt` con:

```
📊 RESUMEN
   Tablas encontradas: 15
   Consultas encontradas: 23

📁 TABLAS:
   - CSR_Modulos
   - CSR_Mantenimientos
   - CSR_Kilometrajes

📋 CSR_Modulos
   Registros: 86
   
   ESTRUCTURA:
   Campo           Tipo        Tamaño    Nulo
   NumModulo       INTEGER     4         No
   Tipo            VARCHAR     50        Sí
   KmTotal         DOUBLE      8         Sí
   
   DATOS DE EJEMPLO:
   Fila 1:
      NumModulo: 1
      Tipo: CUADRUPLA
      KmTotal: 1285885
```

## 📸 Qué Compartir

Una vez generado, compárteme:

1. ✅ Lista de tablas y consultas
2. ✅ Estructura de tabla de Módulos
3. ✅ Estructura de tabla de Mantenimientos
4. ✅ Estructura de tabla de Lecturas/Kms
5. ✅ Ejemplos de datos de cada una

O simplemente todo el contenido de `access_report.txt`.

## 🔧 Troubleshooting

### "ODBC Driver not found"
```powershell
# Instalar Microsoft Access Database Engine
# https://www.microsoft.com/download/details.aspx?id=54920
```

### "pyodbc not found"
```powershell
pip install pyodbc
```

### "Database is locked"
- Cerrar Access
- Nadie más debe estar usando el archivo

## 🎯 Próximo Paso

Con el reporte generado:
1. Identificar tablas correctas
2. Compartir estructura
3. Adaptar código de sincronización a tu estructura exacta
4. ¡Sistema automático funcionando! 🚀

---

**Objetivo**: Mapear tu Access real → Adaptar código → Sincronización robusta y automática

**Duración**: 5 minutos total
