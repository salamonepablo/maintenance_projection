# 🔍 Guía de Exploración de Base Access - Paso a Paso

## 🎯 Objetivo

Conectarnos a tu base Access, ver TODAS las tablas y consultas reales, y entender la estructura exacta para adaptar el código de sincronización.

---

## 📝 Paso 1: Preparación (2 minutos)

### Instalar pyodbc

```powershell
# Abrir PowerShell en tu proyecto
cd C:\Users\pablo.salamone\Programmes\maintenance_projection

# Activar venv
.\.venv\Scripts\Activate.ps1

# Instalar pyodbc
pip install pyodbc
```

**Resultado esperado**: `Successfully installed pyodbc-X.X.X`

---

## 🔌 Paso 2: Verificar Driver de Access (opcional)

Si ya usas Access en tu PC, probablemente ya tienes el driver.

**Si no funciona**, descargar:
- **Microsoft Access Database Engine 2016 Redistributable**
- Link: https://www.microsoft.com/download/details.aspx?id=54920
- Descargar e instalar (2 minutos)

---

## 🚀 Paso 3: Copiar Archivos de Exploración

```powershell
# Ubicarte en la carpeta donde descargaste los archivos
cd C:\Downloads\access_sync

# Copiar a tu proyecto
Copy-Item "explore_access.py" "C:\Users\pablo.salamone\Programmes\maintenance_projection\"
Copy-Item "Explore-Access.ps1" "C:\Users\pablo.salamone\Programmes\maintenance_projection\"
```

---

## 🔍 Paso 4: Ejecutar Exploración

```powershell
# En tu proyecto
cd C:\Users\pablo.salamone\Programmes\maintenance_projection

# Ejecutar explorador (reemplaza la ruta con tu Access real)
.\Explore-Access.ps1 -AccessPath "C:\Ruta\A\Tu\Base\Access.accdb"
```

**Ejemplo real**:
```powershell
.\Explore-Access.ps1 -AccessPath "\\red\compartida\SRMR\Flota.accdb"
```

---

## 📊 Paso 5: Revisar Reporte Generado

El script genera un archivo: **`access_report.txt`**

Este archivo contiene:

```
==================================================
REPORTE DE BASE DE DATOS ACCESS
==================================================
Archivo: C:\...\tu_base.accdb
Fecha: 19/12/2025 15:30:00
==================================================

📊 RESUMEN
   Tablas encontradas: 15
   Consultas encontradas: 23

📁 TABLAS:
   - CSR_Modulos
   - CSR_Mantenimientos
   - CSR_Kilometrajes
   ... etc

🔍 CONSULTAS/VISTAS:
   - qry_ModulosActivos
   - qry_MantenimientosPendientes
   ... etc

==================================================
DETALLE DE TABLAS
==================================================

📋 CSR_Modulos
------------------------------------------------
   Registros: 86

   ESTRUCTURA:
   Campo                          Tipo                 Tamaño     Nulo
   ------------------------------ -------------------- ---------- -----
   ID                             COUNTER              4          No
   NumModulo                      INTEGER              4          No
   Tipo                           VARCHAR              50         Sí
   FechaAlta                      DATETIME             8          Sí
   KmTotal                        DOUBLE               8          Sí

   DATOS DE EJEMPLO (primeras 3 filas):
   
   Fila 1:
      ID: 1
      NumModulo: 1
      Tipo: CUADRUPLA
      FechaAlta: 15/06/2015 00:00
      KmTotal: 1285885.0
   
   ... etc
```

---

## 📸 Paso 6: Capturas para Compartir

Necesito que compartas **capturas o el contenido** de estas secciones del reporte:

### A) Lista de Tablas y Consultas
```
📁 TABLAS:
   - (todos los nombres)

🔍 CONSULTAS/VISTAS:
   - (todos los nombres)
```

### B) Estructura de las Tablas/Consultas Principales

**Busca las tablas/consultas que probablemente contienen**:

1. **Datos de Módulos** (busca nombres como):
   - CSR_Modulos / Modulos / tblModulos
   - Coches / Formaciones / Unidades
   
2. **Eventos de Mantenimiento** (busca):
   - Mantenimientos / Eventos / Intervenciones
   - Historial / Registro
   
3. **Lecturas de Kilometraje** (busca):
   - Kilometrajes / Lecturas / Odometro
   - KMs / Recorridos

Para cada una, comparte:
- ✅ Nombre completo de la tabla/consulta
- ✅ Lista de campos (columnas)
- ✅ Ejemplo de 2-3 filas de datos

---

## 🤔 ¿Cómo Identificar las Tablas Correctas?

### Tabla de Módulos debe tener:
- ✅ Número de módulo (1-86)
- ✅ Tipo (Cuádrupla/Tripla)
- ✅ Fecha de alta o puesta en servicio
- ✅ Kilometraje acumulado (opcional)

### Tabla de Mantenimientos debe tener:
- ✅ Referencia al módulo
- ✅ Tipo de mantenimiento (IQ, B, A, BI, P, DE o similar)
- ✅ Fecha del evento
- ✅ Kilometraje al momento del evento

### Tabla de Lecturas debe tener:
- ✅ Referencia al módulo
- ✅ Fecha de lectura
- ✅ Kilometraje leído

---

## 🎯 Información Mínima que Necesito

Para adaptar el código, necesito saber:

1. **Nombres reales** de las tablas/consultas
2. **Nombres reales** de las columnas
3. **Tipo de datos** de cada columna
4. **Ejemplo de 2-3 filas** para ver formato

Con esto podré adaptar:
```python
# De esto (ejemplo genérico):
query = "SELECT ID_Modulo, TipoModulo FROM tblModulos"

# A esto (tu estructura real):
query = "SELECT NumeroModulo, Tipo FROM CSR_Coches"
```

---

## ⚡ Ejecución Rápida (Todo en Uno)

```powershell
# 1. Navegar a proyecto
cd C:\Users\pablo.salamone\Programmes\maintenance_projection

# 2. Activar venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar pyodbc (si no está)
pip install pyodbc

# 4. Explorar (reemplaza la ruta)
.\Explore-Access.ps1 -AccessPath "\\red\compartida\SRMR\Flota.accdb"

# 5. Abrir reporte
notepad access_report.txt
```

---

## 🚨 Posibles Errores y Soluciones

### Error: "ODBC Driver not found"
**Solución**: Instalar Microsoft Access Database Engine
- https://www.microsoft.com/download/details.aspx?id=54920

### Error: "Database is locked"
**Solución**: 
- Cerrar Access si está abierto
- Verificar que nadie más esté usando el archivo

### Error: "pyodbc not found"
**Solución**:
```powershell
pip install pyodbc
```

### Error: "Script explore_access.py not found"
**Solución**: 
- Copiar explore_access.py al directorio del proyecto

---

## 📤 Qué Compartir Conmigo

Una vez generado el reporte, compárteme:

1. **Captura del inicio del reporte**:
   - Lista de tablas
   - Lista de consultas

2. **Captura de la tabla de Módulos**:
   - Estructura completa
   - Datos de ejemplo

3. **Captura de la tabla de Mantenimientos**:
   - Estructura completa
   - Datos de ejemplo

4. **Captura de la tabla de Lecturas/Kilometrajes**:
   - Estructura completa
   - Datos de ejemplo

O simplemente pega el contenido del archivo `access_report.txt` completo.

---

## ✨ Siguiente Paso

Una vez que tengas el reporte:
1. Revísalo
2. Identifica las tablas/consultas correctas
3. Compárteme las capturas o el texto
4. Yo adaptaré el código de sincronización a tu estructura exacta

¡Vamos paso a paso y quedará perfecto! 🎯

---

**Notas**:
- El script es **solo lectura**, no modifica nada
- Toma ~30 segundos en ejecutar
- El reporte se guarda en `access_report.txt`
