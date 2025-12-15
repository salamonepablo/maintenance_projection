# Arquitectura de Base de Datos - Maintenance Projection

## 🏗️ Diseño General

Sistema de base de datos relacional diseñado para gestionar el ciclo completo de mantenimiento preventivo de material rodante ferroviario.

### Principios de Diseño

1. **Disparador Dual**: Cada perfil de mantenimiento puede dispararse por tiempo O kilometraje (el que ocurra primero)
2. **Auditoría Completa**: Registros transaccionales de todas las lecturas y eventos
3. **Integridad Referencial**: Foreign Keys estrictas con `CASCADE` y `PROTECT` según criticidad
4. **Escalabilidad**: Preparado para extenderse a toda la flota (no solo CSR)

## 📊 Diagrama de Entidades

```
MaintenanceProfile (Perfiles de Mantenimiento)
    ├── code: IQ, B, A, BI, P, DE (UNIQUE)
    ├── km_interval: nullable
    └── time_interval_days: nullable

FleetModule (Módulos de Flota)
    ├── id: 01-86 (PRIMARY KEY)
    ├── module_type: CUADRUPLA / TRIPLA
    ├── total_accumulated_km: calculado automático
    └── in_service_date

MaintenanceEvent (Eventos de Mantenimiento)
    ├── fleet_module (FK → FleetModule, CASCADE)
    ├── profile (FK → MaintenanceProfile, PROTECT)
    ├── event_date
    ├── odometer_km
    └── UNIQUE(fleet_module, profile, event_date)

OdometerLog (Lecturas de Odómetro)
    ├── fleet_module (FK → FleetModule, CASCADE)
    ├── reading_date
    ├── odometer_reading
    ├── daily_delta_km (AUTO-calculado)
    └── UNIQUE(fleet_module, reading_date)
```

## 🔄 Flujos de Datos Críticos

### 1. Alta de Lectura de Odómetro

```python
# Al guardar OdometerLog:
1. compute_daily_delta()  # Calcula km desde última lectura
2. save()                  # Guarda en BD
3. module.update_accumulated_km()  # Actualiza total en FleetModule
```

**Trigger**: `OdometerLog.save()` automáticamente actualiza `FleetModule.total_accumulated_km`

### 2. Proyección de Próxima Intervención

```python
ProjectionService.project_next_due(module, profile):
    1. Buscar último MaintenanceEvent del perfil
    2. Calcular fecha por tiempo: last_event + time_interval_days
    3. Calcular fecha por km: hoy + (km_faltante / promedio_30d)
    4. Retornar min(fecha_tiempo, fecha_km)
```

## 🗄️ Estrategia de Base de Datos

### Desarrollo Local

**Opción 1: SQLite (rápido, sin instalación)**
```bash
# .env
# DATABASE_URL no definido → usa db.sqlite3
DEBUG=True
```

**Opción 2: PostgreSQL (recomendado, igual a producción)**
```bash
# Instalar PostgreSQL 14+
# Crear usuario y base:
createdb maintenance_db
createuser maintenance_user -P

# .env
DATABASE_URL=postgres://maintenance_user:password@localhost:5432/maintenance_db
DEBUG=True
```

### Producción

**PostgreSQL Obligatorio**
```bash
# Razones:
# 1. Compatibilidad con sistema PHP/PostgreSQL de GTI
# 2. Concurrencia real para múltiples usuarios
# 3. Features avanzadas (Foreign Data Wrappers, schemas, etc.)
# 4. Backup y replicación empresarial
```

## 🔗 Estrategia de Integración con Sistema PHP/PostgreSQL de GTI

### Escenario 1: Base de Datos Compartida (Recomendado para PoC)

```sql
-- Usar esquemas para separar lógicamente
CREATE SCHEMA maintenance;
CREATE SCHEMA legacy_php;  -- Sistema existente

-- Tablas Django en schema maintenance
ALTER TABLE fleet_module SET SCHEMA maintenance;
-- etc.

-- Permite queries cross-schema:
SELECT m.id, l.some_field
FROM maintenance.fleet_module m
JOIN legacy_php.some_table l ON ...
```

**Ventajas**:
- Transacciones ACID entre sistemas
- Queries directas sin overhead
- Un solo backup

**Desventajas**:
- Acopla ambos sistemas
- Migraciones coordinadas

### Escenario 2: Bases Separadas con Foreign Data Wrappers

```sql
-- En BD Django:
CREATE EXTENSION postgres_fdw;

CREATE SERVER legacy_php_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'legacy_db.local', dbname 'php_maintenance', port '5432');

CREATE FOREIGN TABLE legacy_vehicles (
    id INT,
    plate VARCHAR(50)
) SERVER legacy_php_server OPTIONS (schema_name 'public', table_name 'vehicles');

-- Ahora puedes joinear con tablas locales:
SELECT fm.id, lv.plate
FROM maintenance_fleetmodule fm
JOIN legacy_vehicles lv ON fm.legacy_id = lv.id;
```

**Ventajas**:
- Sistemas desacoplados
- Migraciones independientes
- Rollback sin afectar legacy

**Desventagas**:
- Overhead de red en queries
- No transacciones distribuidas nativas

### Escenario 3: API REST entre Sistemas

```python
# Django consume API del sistema PHP
import requests

def sync_with_legacy():
    response = requests.get('https://legacy.gti/api/vehicles')
    vehicles = response.json()
    # Sincronizar con FleetModule
```

**Ventajas**:
- Máximo desacople
- Puede ser async
- Tecnologías independientes

**Desventajas**:
- Latencia
- Eventual consistency
- Más complejo

## 📈 Recomendación para Presentación a Gerencia

1. **Fase 1 - PoC (Actual)**
   - PostgreSQL local (localhost)
   - Datos CSR importados
   - Django Admin funcional
   - Proyecciones básicas

2. **Fase 2 - Piloto Interno**
   - PostgreSQL en servidor interno
   - Schema `maintenance` separado
   - Acceso web (Intranet)
   - Reportes básicos

3. **Fase 3 - Integración GTI**
   - Evaluar con GTI: Schema compartido vs Foreign Data Wrappers
   - Migrar datos históricos del sistema PHP
   - SSO/LDAP corporativo
   - Dashboards con Django + Chart.js o similar

## 🔒 Consideraciones de Seguridad

### Desarrollo
- `.env` en `.gitignore` (✓ ya configurado)
- `DEBUG=True` solo en local
- `SECRET_KEY` diferente por entorno

### Producción
- `DEBUG=False` obligatorio
- PostgreSQL con SSL/TLS
- Usuarios BD con permisos mínimos (no superuser)
- Backup diario automático
- Logs de auditoría de cambios críticos

## 📝 Migraciones

```bash
# Generar migraciones
python manage.py makemigrations maintenance

# Ver SQL antes de aplicar
python manage.py sqlmigrate maintenance 0001

# Aplicar migraciones
python manage.py migrate

# Rollback (si es necesario)
python manage.py migrate maintenance 0001  # Volver a migración específica
```

## 🧪 Testing de BD

```bash
# Tests usan BD temporal in-memory (SQLite)
python manage.py test maintenance

# Para forzar PostgreSQL en tests:
# settings.py test override o usar --keepdb
python manage.py test --keepdb  # Reutiliza BD entre runs
```

## 📊 Índices y Performance

Django automáticamente crea índices en:
- Primary Keys
- Foreign Keys
- Campos con `unique=True`

Para queries frecuentes, considerar:
```python
class Meta:
    indexes = [
        models.Index(fields=['reading_date', 'fleet_module']),
        models.Index(fields=['event_date', 'profile']),
    ]
```

## 🔍 Queries de Diagnóstico

```sql
-- Ver tamaño de tablas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'maintenance'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Verificar integridad referencial
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f' AND connamespace = 'maintenance'::regnamespace;

-- Módulos sin lecturas (data quality check)
SELECT fm.id, fm.module_type
FROM maintenance_fleetmodule fm
LEFT JOIN maintenance_odometerlog ol ON fm.id = ol.fleet_module_id
WHERE ol.id IS NULL;
```
