# Guía de Diagnóstico y Corrección - Windows

## 🔧 Problema de Encoding Resuelto

Los scripts ahora tienen versión **sin emojis** para evitar problemas con Windows.

## 📋 Paso a Paso

### 1. Copiar scripts al proyecto

Copiar estos archivos a la raíz del proyecto (donde está `manage.py`):
- `diagnose_data_win.py`
- `fix_corrupt_deltas_win.py`
- `views_fixed.py`

### 2. Ejecutar Diagnóstico

Abrir PowerShell en la raíz del proyecto:

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Iniciar shell de Django
python manage.py shell
```

Dentro del shell de Django:

```python
# Ejecutar diagnóstico
exec(open('diagnose_data_win.py', encoding='utf-8').read())
```

**Salida esperada:**
```
================================================================================
DIAGNOSTICO DE DATOS DE ODOMETRO
================================================================================

1. DELTAS NEGATIVOS (Lecturas que disminuyen)
--------------------------------------------------------------------------------
[ERROR] Se encontraron 235 registros con delta negativo:
Modulo     Fecha        Lectura         Delta          
--------------------------------------------------------------------------------
01         2025-12-15     1,291,286      -12,450
03         2025-12-18     1,471,276      -8,320
...
```

### 3. Analizar Resultados

Si el diagnóstico muestra:
- ✅ **0 deltas negativos** → Solo aplicar `views_fixed.py`
- ❌ **Múltiples deltas negativos** → Ejecutar script de corrección

### 4. Corregir Datos (Si es necesario)

**Opción A: Simulación (recomendado primero)**

```python
exec(open('fix_corrupt_deltas_win.py', encoding='utf-8').read())
recalculate_all_deltas(dry_run=True)
```

Esto muestra qué cambios haría **sin modificar la BD**.

**Opción B: Fix Rápido (si son pocos)**

```python
quick_fix_negatives()
# Escribir 'SI' para confirmar
```

Esto pone en `0` todos los deltas negativos.

**Opción C: Recálculo Completo**

⚠️ **IMPORTANTE:** Hacer backup de la BD primero

```python
recalculate_all_deltas(dry_run=False)
# Escribir 'SI' para confirmar
```

Esto recalcula **todos** los deltas desde cero.

### 5. Actualizar views.py

Una vez corregidos los datos (o si no hay corrupción):

```powershell
# En PowerShell (FUERA del shell de Django)
# Hacer backup
cp maintenance/views.py maintenance/views.py.backup

# Aplicar fix
cp views_fixed.py maintenance/views.py
```

### 6. Reiniciar servidor

```powershell
python manage.py runserver
```

### 7. Verificar Dashboard

Abrir: http://localhost:8000/maintenance/

**Verificar:**
- ✅ Kilometrajes mensuales positivos
- ✅ Promedios diarios realistas (500-2000 km/día)
- ✅ Sin valores negativos

## 🐛 Troubleshooting

### Error: "cannot contain null bytes"

**Causa:** Archivo con encoding incorrecto

**Solución:** Usar versión `_win.py` y especificar `encoding='utf-8'`:
```python
exec(open('diagnose_data_win.py', encoding='utf-8').read())
```

### Error: "UnicodeDecodeError"

**Causa:** Archivo con caracteres especiales

**Solución:** Los archivos `_win.py` no tienen emojis/caracteres especiales.

### Deltas negativos persisten

**Posibles causas:**
1. Lecturas con fechas desordenadas en CSV original
2. Odómetro reseteado (cambio de unidad/módulo)
3. Error en importación legacy

**Solución:** Ejecutar recálculo completo con `recalculate_all_deltas(dry_run=False)`

## 📊 Interpretación de Resultados

### Diagnóstico Normal
```
Total deltas del mes:         245,832 km
[OK] El total del mes es positivo
[OK] No hay modulos con deltas negativos
```

### Diagnóstico con Problemas
```
Total deltas del mes:     -26,904,013 km
[ERROR] El total del mes es NEGATIVO
[ERROR] Se encontraron 235 registros con delta negativo
```

## ⚙️ Comandos Rápidos

```python
# Diagnóstico
exec(open('diagnose_data_win.py', encoding='utf-8').read())

# Simulación de fix
exec(open('fix_corrupt_deltas_win.py', encoding='utf-8').read())
recalculate_all_deltas(dry_run=True)

# Aplicar fix
recalculate_all_deltas(dry_run=False)

# Fix rápido
quick_fix_negatives()
```

## 🔄 Rollback

Si algo sale mal después de aplicar cambios:

```powershell
# Restaurar views.py
cp maintenance/views.py.backup maintenance/views.py

# Restaurar BD (si tienes backup)
# Depende de tu sistema de BD
```

## ✅ Checklist Final

- [ ] Diagnóstico ejecutado sin errores
- [ ] Deltas negativos corregidos (si existían)
- [ ] `views_fixed.py` aplicado en `maintenance/views.py`
- [ ] Servidor reiniciado
- [ ] Dashboard muestra valores positivos
- [ ] Backup de BD guardado (recomendado)
