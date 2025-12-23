# 📊 Sistema de Sincronización Access → Django

Sincronización automática entre base Access (DB_CCEE_Mantenimiento) y Django para proyección de mantenimiento ferroviario CSR.

---

## 🎯 Características

✅ **Sincronización bidireccional segura** (Django lee, Access no se modifica)  
✅ **Mapeo automático de ciclos** (IQ/IB/AN/BA/RS → IQ/B/A/BI/P)  
✅ **Filtrado inteligente** (Solo CSR, excluye Toshiba)  
✅ **Sincronización incremental** (Solo datos nuevos/modificados)  
✅ **Modo prueba** (Ver cambios sin aplicarlos)  
✅ **Transacciones atómicas** (Todo o nada, no corrupción)

---

## 📂 Archivos

```
access_sync_final/
├── access_extractor.py         # Servicio de extracción de Access
├── sync_from_access.py          # Comando Django de sincronización
├── settings_access_config.py    # Configuración para settings.py
├── INSTALACION.md               # Guía paso a paso
├── README.md                    # Este archivo
└── EJEMPLOS.md                  # Casos de uso
```

---

## ⚡ Quick Start

### 1. Instalar

```powershell
# Copiar archivos
Copy-Item access_extractor.py maintenance/services/
Copy-Item sync_from_access.py maintenance/management/commands/

# Configurar settings.py (ver INSTALACION.md)
```

### 2. Crear Perfiles

```powershell
python manage.py shell
```

```python
from maintenance.models import MaintenanceProfile

profiles = [
    {'cycle_type': 'IQ', 'km_interval': 6250, 'time_interval_days': 15},
    {'cycle_type': 'B', 'km_interval': 25000, 'time_interval_days': 60},
    {'cycle_type': 'A', 'km_interval': 187500, 'time_interval_days': 456},
    {'cycle_type': 'BI', 'km_interval': 375000, 'time_interval_days': 912},
    {'cycle_type': 'P', 'km_interval': 750000, 'time_interval_days': 1825},
    {'cycle_type': 'DE', 'km_interval': 1500000, 'time_interval_days': 3650},
]

for p in profiles:
    MaintenanceProfile.objects.get_or_create(**p)
```

### 3. Sincronizar

```powershell
# Primera vez (todo)
python manage.py sync_from_access --full

# Diario (incremental)
python manage.py sync_from_access
```

---

## 💡 Casos de Uso

### Caso 1: Setup Inicial

```powershell
# 1. Test de conexión
python manage.py sync_from_access --test

# 2. Ver qué se sincronizaría
python manage.py sync_from_access --full --test

# 3. Sincronizar todo
python manage.py sync_from_access --full
```

### Caso 2: Actualización Matutina (Diaria)

```powershell
# Sincroniza eventos de últimos 30 días y lecturas de últimos 7 días
python manage.py sync_from_access
```

### Caso 3: Solo Lecturas Nuevas

```powershell
# Útil después de tomar lecturas en Access
python manage.py sync_from_access --readings-only
```

### Caso 4: Recuperar Evento Específico

```powershell
# Sincronizar desde fecha específica
python manage.py sync_from_access --events-only --since 2025-01-15
```

### Caso 5: Agregar Nuevos Módulos

```powershell
# Si se agregan módulos en Access
python manage.py sync_from_access --modules-only
```

---

## 🔍 Estructura de Datos

### Access (Origen)

```
A_00_Kilometrajes
├── Módulo: M01, M02... (CSR) | T01, T02... (Toshiba)
├── Kilometraje: 1250000
└── Fecha: 2025-12-19

A_00_OT_Consulta
├── Módulos: M01, M02...
├── Tarea: IQ, IB, AN, BA, RS (primeros 2 caracteres)
├── Km: 1250000
└── Fecha Fin: 2025-12-19
```

### Django (Destino)

```python
FleetModule
├── module_number: 1, 2, 3...
├── module_type: CUADRUPLA (1-42) | TRIPLA (43-86)
└── is_active: True

MaintenanceEvent
├── module: FK → FleetModule
├── profile: FK → MaintenanceProfile
├── event_date: 2025-12-19
└── odometer_km: 1250000

OdometerLog
├── module: FK → FleetModule
├── reading_date: 2025-12-19
└── odometer_reading: 1250000
```

---

## 🎨 Mapeo de Ciclos

| Access | Django | Descripción | Intervalo |
|--------|--------|-------------|-----------|
| IQ | IQ | Quincenal | 6,250 km / 15 días |
| IB | B | Bimestral | 25,000 km / 60 días |
| AN | A | Anual | 187,500 km / ~15 meses |
| BA | BI | Bianual | 375,000 km / ~2.5 años |
| RS | P | Pentanual | 750,000 km / ~5 años |
| #N/A | DE | Decanual | 1,500,000 km / ~10 años |

**Nota**: La columna "Tarea" en Access puede tener números al final (ej: "IQ1", "AN2"). 
Solo se usan los **primeros 2 caracteres** para el mapeo.

---

## 📊 Filtros Aplicados

### Solo CSR
```sql
WHERE Módulo LIKE 'M%'      -- En A_00_Kilometrajes
WHERE Módulos LIKE 'M%'     -- En A_00_OT_Consulta
```

### Exclusiones
- ❌ Módulos Toshiba (T01, T02...)
- ❌ Registros sin fecha
- ❌ Registros sin kilometraje
- ❌ Tareas no reconocidas (que no sean IQ/IB/AN/BA/RS)

---

## 🔄 Flujo de Sincronización

```
Access DB
   ↓
[AccessExtractor]
   ├─ Conectar (ReadOnly)
   ├─ Filtrar CSR (M%)
   ├─ Extraer datos
   └─ Mapear ciclos
   ↓
[Django Command]
   ├─ Validar datos
   ├─ Buscar FK (módulos, perfiles)
   ├─ get_or_create (evita duplicados)
   └─ Transacción atómica
   ↓
Django Models
   ├─ FleetModule
   ├─ MaintenanceEvent
   └─ OdometerLog
   ↓
Dashboard
   ├─ Proyecciones
   ├─ Alertas
   └─ Estadísticas
```

---

## 🛡️ Seguridad

### Protecciones Implementadas
- ✅ **ReadOnly**: No modifica Access
- ✅ **Transacciones atómicas**: Rollback en caso de error
- ✅ **Validaciones**: Datos validados antes de insertar
- ✅ **get_or_create**: Evita duplicados
- ✅ **FK constraints**: Solo inserta si existen referencias

### Qué NO Hace
- ❌ No modifica Access
- ❌ No borra datos de Django
- ❌ No sobrescribe datos existentes (usa get_or_create)

---

## 📈 Performance

| Operación | Registros | Tiempo |
|-----------|-----------|--------|
| Módulos (primera vez) | ~86 | 5-10 seg |
| Eventos (full) | ~1000 | 1-2 min |
| Lecturas (full) | ~5000 | 2-3 min |
| Incremental diaria | ~50-200 | 10-30 seg |

**Tips de Optimización**:
- Usar `--since` para limitar rango de fechas
- Sincronizar solo lo necesario (`--modules-only`, etc.)
- Ejecutar en horarios de baja carga

---

## 🐛 Debugging

### Ver qué se sincronizaría (sin modificar)

```powershell
python manage.py sync_from_access --test
```

### Ver logs detallados

Agregar en settings.py:

```python
ACCESS_SYNC_CONFIG = {
    'VERBOSE_LOGGING': True,
}
```

### Verificar conexión

```powershell
python -c "
from maintenance.services.access_extractor import AccessExtractor
from django.conf import settings

with AccessExtractor(settings.ACCESS_CONNECTION_STRING) as ext:
    stats = ext.test_connection()
    print(stats)
"
```

---

## 🔗 Enlaces

- **INSTALACION.md**: Guía paso a paso de instalación
- **Dashboard**: http://localhost:8000/maintenance/projection/
- **Admin Django**: http://localhost:8000/admin

---

## 📞 Soporte

**Problemas comunes**: Ver sección Troubleshooting en INSTALACION.md

**Para reportar issues**:
1. Comando ejecutado
2. Error completo
3. Output de `--test`

---

## ✅ Validación Post-Instalación

```powershell
# 1. Test de conexión
python manage.py sync_from_access --test

# 2. Verificar módulos en admin
# http://localhost:8000/admin/maintenance/fleetmodule/
# Debe haber ~86 módulos CSR

# 3. Verificar eventos
# http://localhost:8000/admin/maintenance/maintenanceevent/
# Debe haber eventos con tipos IQ, B, A, BI, P

# 4. Ver dashboard
# http://localhost:8000/maintenance/projection/
# Debe mostrar proyecciones
```

---

**Sistema listo para producción** ✅
