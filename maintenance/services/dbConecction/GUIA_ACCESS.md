# 🔍 Guía para Explorar Access y Decidir Qué Tablas Usar

## 🎯 Objetivo
Entrar al backend Access y ver exactamente qué consultas/tablas tienen los datos que necesitas.

---

## 📂 PASO 1: Abrir el Backend en Access

### Método A: Solo Lectura (Recomendado)
```
1. Cerrar el frontend si está abierto
2. Abrir Microsoft Access
3. Archivo → Abrir
4. Navegar a: G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\
5. Seleccionar: DB_CCEE_Mantenimiento 1.0.accdb
6. Hacer clic en la FLECHA junto a "Abrir"
7. Seleccionar: "Abrir como solo lectura"
8. Ingresar contraseña: 0733
```

### Método B: Desde el Frontend
```
1. Abrir tu frontend: Programación CCEE V3.4.accde
2. Ir a: Herramientas de base de datos → Administrador de tablas vinculadas
3. Hacer clic derecho en cualquier tabla → "Administrador de tablas vinculadas"
4. Esto te mostrará dónde está el backend
5. Cerrar el frontend
6. Abrir el backend con Método A
```

---

## 🔎 PASO 2: Navegar en Access

Una vez abierto el backend, verás el panel izquierdo con:

```
Todos los objetos de Access
├─ 📊 Tablas              ← Datos en crudo
├─ 🔍 Consultas           ← ESTO ES LO MÁS IMPORTANTE
├─ 📋 Formularios         ← Solo para el frontend
├─ 📄 Informes            ← Solo para el frontend
└─ ...
```

**Haz clic en "Consultas"** - Ahí están las queries armadas.

---

## 📝 PASO 3: Identificar Consultas Útiles

### Busca consultas con nombres como:

**Para MÓDULOS:**
- `qry_Modulos`
- `qry_ModulosCSR`
- `qry_ModulosActivos`
- `Consulta_Modulos`
- Cualquier cosa con "Modulo" o "CSR"

**Para MANTENIMIENTOS:**
- `qry_Mantenimientos`
- `qry_MantenimientosCSR`
- `qry_InspeccionesCSR`
- `qry_CiclosMantenimiento`
- `qry_IQ_B_A` (o similar)
- Cualquier cosa con "Mantenimiento", "Inspeccion", "Ciclo"

**Para KILOMETRAJES:**
- `qry_Kilometrajes`
- `qry_KilometrajesCSR`
- `qry_LecturasKm`
- `qry_OdometrosCSR`
- Cualquier cosa con "Kilometr", "Km", "Lectura"

---

## 🔍 PASO 4: Inspeccionar una Consulta

Para cada consulta que parezca útil:

1. **Hacer doble clic** en la consulta
   → Se abrirá mostrando los datos

2. **Ver columnas disponibles**
   → Scroll horizontal para ver todos los campos

3. **Ver si tiene datos de CSR**
   → Buscar módulos M01, M02, etc. o T04, T06, etc.

4. **Anotar nombre y campos**
   → Ejemplo:
   ```
   Consulta: qry_MantenimientosCSR
   Campos: Modulo, FechaMantenimiento, TipoMantenimiento, Kilometraje
   Ejemplo de datos: M01, 15/12/2024, IQ, 1250000
   ```

5. **Ver el SQL** (opcional pero útil)
   - Hacer clic derecho en la consulta
   - "Vista Diseño" → Muestra las tablas que usa
   - O "Vista SQL" → Muestra el query completo

---

## 📸 PASO 5: Documentar Lo Que Encuentres

Para cada consulta útil, anota o toma captura de:

### Opción A: Lista Simple
```
✓ CONSULTA 1: qry_MantenimientosCSR
  Campos: Modulo, Fecha, Tipo, Kilometraje
  Registros: ~500
  Notas: Tiene IQ, B, A claramente identificados
  
✓ CONSULTA 2: qry_LecturasKmCSR
  Campos: Modulo, Fecha, Lectura_Km
  Registros: ~2000
  Notas: Lecturas mensuales de odómetro
```

### Opción B: Capturas de Pantalla
Toma capturas de:
1. Lista de consultas disponibles
2. Vista de datos de cada consulta relevante
3. Vista Diseño (opcional) para ver qué tablas usa

---

## 💡 PASO 6: Compartir Conmigo

Una vez que identifiques las consultas, compárteme:

### Información Mínima:
```
CONSULTA PARA MÓDULOS:
Nombre: ___________________
Campos principales: ___________________

CONSULTA PARA MANTENIMIENTOS:
Nombre: ___________________
Campos principales: ___________________
Tipos de ciclo que aparecen: ___________________

CONSULTA PARA KILOMETRAJES:
Nombre: ___________________
Campos principales: ___________________
```

### Información Ideal (si puedes):
- Capturas de pantalla de las consultas con datos
- O export de 5-10 filas de ejemplo de cada consulta
- O descripción detallada de qué ves

---

## 🚀 Alternativa Rápida: Script Python

Si prefieres no abrir Access, ejecuta:

```powershell
python ver_consultas.py
```

Este script lista todas las consultas disponibles con sus campos.

---

## ❓ Qué Buscar Específicamente

### Para el Dashboard de Proyección Necesito:

**1. Módulos CSR (M01-M86 o T##)**
- ✅ Lista de módulos activos
- ✅ Tipo de módulo (Cuádrupla/Tripla)
- ✅ Kilometraje acumulado actual (opcional)

**2. Eventos de Mantenimiento**
- ✅ Módulo
- ✅ Fecha del evento
- ✅ Tipo de ciclo (IQ, B, A, BI, P, DE)
- ✅ Kilometraje al momento del evento

**3. Lecturas de Odómetro**
- ✅ Módulo
- ✅ Fecha de lectura
- ✅ Kilometraje leído
- ✅ Frecuencia (diaria, semanal, mensual)

---

## 🎯 Resultado Esperado

Al final de este proceso sabremos:

✓ Consulta exacta para leer módulos  
✓ Consulta exacta para leer mantenimientos  
✓ Consulta exacta para leer kilometrajes  
✓ Estructura real de tus datos  
✓ Cómo calcular proyecciones con TU información  

Y podré escribir el código de sincronización perfecto para tu caso.

---

## 📞 Ayuda

Si tienes dudas o no encuentras algo:
- Comparte capturas de lo que ves
- Describe con tus palabras qué consultas hay
- O ejecuta el script `ver_consultas.py` y comparte el resultado

---

**¡Adelante! Explora el Access y cuéntame qué encontraste** 🔍
