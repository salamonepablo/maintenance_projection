# 🔧 Fix: Kilometrajes Negativos en Dashboard

## 🔴 Problema Identificado

El dashboard muestra **-26.904.013 km** recorridos en diciembre y **-13.015 km/día** de promedio.

### Causas raíz encontradas:

1. **Cálculo manual de diferencias** en lugar de usar `daily_delta_km`
2. **Naming confuso**: variable `module_id` que en realidad es un objeto `FleetModule`
3. **Sin validación** de valores negativos (datos corruptos)

## ✅ Soluciones Implementadas

### 1. Usar `daily_delta_km` pre-calculado

#### ❌ ANTES (incorrecto):
```python
month_logs = OdometerLog.objects.filter(
    fleet_module=module_id,
    reading_date__gte=first_day_of_month
).order_by('reading_date')

first_reading = month_logs.first()
last_reading = month_logs.last()

if first_reading and last_reading:
    km_this_month = last_reading.odometer_reading - first_reading.odometer_reading
```

**Problemas:**
- Si las lecturas están desordenadas → resultado negativo
- Si hay gaps en las lecturas → cálculo incorrecto
- Ignora los deltas ya calculados en `OdometerLog.save()`

#### ✅ DESPUÉS (correcto):
```python
month_deltas = OdometerLog.objects.filter(
    fleet_module=module,
    reading_date__gte=first_day_of_month
).values_list('daily_delta_km', flat=True)

# Sumar deltas positivos (ignora None y negativos por datos corruptos)
km_this_month = sum(km for km in month_deltas if km is not None and km > 0)
```

**Ventajas:**
- Usa el delta pre-calculado en `compute_daily_delta()`
- Filtra datos corruptos (negativos)
- Más eficiente (solo trae un campo)

### 2. Promedio diario mejorado

#### ❌ ANTES:
```python
recent_logs = OdometerLog.objects.filter(
    fleet_module=module_id,
    reading_date__gte=thirty_days_ago
).order_by('reading_date')

first_recent = recent_logs.first()
last_recent = recent_logs.last()

if first_recent and last_recent and first_recent != last_recent:
    days_diff = (last_recent.reading_date - first_recent.reading_date).days
    if days_diff > 0:
        km_diff = last_recent.odometer_reading - first_recent.odometer_reading
        daily_avg = km_diff / days_diff
```

#### ✅ DESPUÉS:
```python
recent_deltas = OdometerLog.objects.filter(
    fleet_module=module,
    reading_date__gte=thirty_days_ago
).values_list('daily_delta_km', 'reading_date')

# Filtrar solo deltas positivos
valid_deltas = [km for km, _ in recent_deltas if km is not None and km > 0]

if valid_deltas:
    daily_avg = sum(valid_deltas) / len(valid_deltas)
else:
    daily_avg = 0
```

### 3. Km desde último evento

#### ❌ ANTES:
```python
events_after = OdometerLog.objects.filter(
    fleet_module=module_id,
    reading_date__gte=last_event.event_date
).order_by('reading_date')

first_after = events_after.first()
last_after = events_after.last()

if first_after and last_after:
    km_since_event = last_after.odometer_reading - last_event.odometer_km
else:
    km_since_event = module_id.total_accumulated_km - last_event.odometer_km
```

#### ✅ DESPUÉS:
```python
# Usar el acumulado directamente
current_km = module.total_accumulated_km
km_since_event = current_km - last_event.odometer_km

# Validación
if km_since_event < 0:
    km_since_event = 0
```

### 4. Naming claro

#### ❌ ANTES:
```python
for module_id in modules_query:  # Confuso: es un objeto, no un ID
    fleet_module=module_id
```

#### ✅ DESPUÉS:
```python
for module in modules_query:  # Claro: es un objeto FleetModule
    fleet_module=module
```

## 🔍 Verificación de Datos Corruptos

Para diagnosticar si hay lecturas con kilometrajes decrecientes, ejecutar:

```bash
python manage.py shell
```

```python
from maintenance.models import OdometerLog

# Buscar deltas negativos
corrupt_logs = OdometerLog.objects.filter(daily_delta_km__lt=0)

print(f"Registros con delta negativo: {corrupt_logs.count()}")

for log in corrupt_logs[:10]:
    print(f"Módulo {log.fleet_module.id:02d} - {log.reading_date}: {log.daily_delta_km:,} km")
```

## 📦 Archivos Modificados

- `views.py` → `views_fixed.py` (versión corregida)

## 🚀 Próximos Pasos

1. **Reemplazar** el archivo `maintenance/views.py` con `views_fixed.py`
2. **Verificar** datos corruptos con script de diagnóstico
3. **Si hay deltas negativos**: revisar importación legacy o corrección manual
4. **Testing**: ejecutar `python manage.py test maintenance`

## 🎯 Resultado Esperado

Después del fix:
- ✅ Kilometrajes mensuales positivos
- ✅ Promedios diarios realistas (500-2000 km/día por módulo)
- ✅ Estadísticas coherentes
- ✅ Código más mantenible
