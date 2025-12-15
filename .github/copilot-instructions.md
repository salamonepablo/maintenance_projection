# Guía para Agentes de IA - Maintenance Projection

## 🎯 Contexto del Proyecto

Sistema Django para proyección de mantenimiento ferroviario de material rodante argentino (Flota CSR). Usa **disparador dual** (tiempo + kilometraje) para predecir próximas intervenciones de mantenimiento.

### Modelos Core (`maintenance/models.py`)

```python
FleetModule        # Módulos 01-86, tipo Cuádrupla (≤42) o Tripla (≥43)
MaintenanceProfile # Ciclos: IQ, B, A, BI, P, DE con intervalos duales
MaintenanceEvent   # Registros de intervenciones con odómetro y fecha
OdometerLog        # Lecturas transaccionales, calcula delta automático
ProjectionService  # Estima próxima intervención (min de tiempo/km)
```

**Regla crítica**: `OdometerLog.save()` automáticamente:
1. Calcula `daily_delta_km` vs lectura previa
2. Actualiza `FleetModule.total_accumulated_km`

### Ciclos de Mantenimiento Normalizados

Definidos en `context/MAINTENANCE_CYCLE.md`:
- **IQ** (Quincenal): 6.250 km / 15 días
- **B** (Bimestral): 25.000 km / 60 días  
- **A** (Anual): 187.500 km / 15 meses
- **BI** (Bianual): 375.000 km / 2.5 años
- **P** (Pentanual): 750.000 km / 5 años
- **DE** (Decanual): 1.500.000 km / 10 años

## 🔧 Comandos de Desarrollo

### Setup inicial (PowerShell en Windows)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configurar BD (PostgreSQL recomendado)
$env:DATABASE_URL = "postgres://user:pass@localhost:5432/maintenance_db"

python manage.py makemigrations maintenance
python manage.py migrate
python manage.py createsuperuser
```

### Importar datos legacy (ETL)
```bash
# Orden crítico: módulos → eventos → lecturas (respeta FKs)
python manage.py import_legacy_data

# Formato CSV esperado (separador: ";", fechas: DD/MM/YYYY)
# CSR_Modulos.csv: FORMACION;MODULO;MC1;R1;R2;MC2
# CSR_MantEvents.csv: Id_Mantenimiento;Módulo;Tipo_Mantenimiento;Fecha;Kilometraje
# CSR_LecturasKms.csv: Id_Kilometrajes;Módulo;kilometraje;Fecha

# Opciones útiles
python manage.py import_legacy_data --clear  # Borra datos previos
python manage.py import_legacy_data --skip-eventos
```

### Testing
```bash
python manage.py test maintenance              # Suite completa
python manage.py test maintenance.tests.test_import_legacy_data
python manage.py test maintenance.tests.test_models
```

## 📐 Patrones de Arquitectura

### Datos legacy: Parseo de formatos
- **Kilometraje**: `"1.285.885,00"` → `1285885` (miles con punto, decimal con coma)
- **Fechas**: `"11/12/2025"` → `date(2025, 12, 11)` (formato DD/MM/YYYY)
- **Módulos**: `"M01"` → `1` (strip "M", cast a int)

### Proyección dual (ProjectionService)
```python
# Retorna la fecha MÁS CERCANA entre:
time_due = last_event.date + profile.time_interval_days
km_due = hoy + ceil((km_faltante) / promedio_diario_30d)
return min(time_due, km_due)  # El que dispare primero
```

### ETL con transacciones atómicas
```python
with transaction.atomic():
    # 1. Módulos (independientes)
    # 2. Eventos (FK a módulos)
    # 3. Lecturas (FK a módulos, actualiza acumulado)
```

## 🚫 Errores Comunes a Evitar

1. **No ejecutar migraciones antes de `import_legacy_data`** → FK constraint fail
2. **Asumir que `maintenance` está en `INSTALLED_APPS`** → Verificar `core/settings.py`
3. **Usar formato de número incorrecto en CSVs** → Mantener `;` separador, formato europeo
4. **Importar lecturas sin ordenar por fecha** → OdometerLog calcula delta secuencialmente
5. **Olvidar activar venv** → Usa `.\.venv\Scripts\Activate.ps1` en PowerShell

## 📝 Convenciones del Proyecto

### Control de versiones
- **SemVer estricto** en `package.json`: MAJOR.MINOR.PATCH
- **Changelog obligatorio** (`CHANGELOG.md`) formato [Keep a Changelog](https://keepachangelog.com/)
- Cada feature nueva/fix requiere bump + entrada en changelog

### Estilo de código
- Type hints Python 3.11+ (`from __future__ import annotations`)
- Docstrings en español con descripción breve + detalles
- Tests con `TestCase` de Django, cobertura mínima de happy path + edge cases
- Principios SOLID cuando sea aplicable (especialmente SRP en servicios)

### Respuestas del agente
- **Siempre en español** (código puede tener nombres en inglés)
- Concisas y directas, al grano
- Incluir ejemplos de código ejecutables cuando sea relevante

## 📂 Estructura Clave

```
maintenance/
├── models.py              # 5 clases: Profile, Module, Event, Log, ProjectionService
├── management/commands/
│   └── import_legacy_data.py  # ETL con pandas + tqdm
├── tests/
│   ├── test_models.py         # Tests de lógica de negocio
│   └── test_import_legacy_data.py  # Tests de importación
└── admin.py               # [Pendiente] Interfaces admin de Django

context/                    # Docs de negocio + CSVs ejemplo
docs/
├── setup.md               # Guía Windows PowerShell
└── maintenance_models.md  # Especificación de modelos
```

## 🔗 Integración Externa

- **Base de datos**: PostgreSQL (prod) / SQLite (dev) via `DATABASE_URL`
- **ETL**: pandas para CSV parsing, tqdm para progress bars
- **Django Admin**: `/admin` endpoint para gestión manual (configurar en `maintenance/admin.py`)

## 🎓 Recursos Internos

- `AGENTS.md`: Instrucciones generales del asistente (principios SOLID, respuestas en español)
- `context/MAINTENANCE_CYCLE.md`: Especificación de intervalos normativos
- `docs/maintenance_models.md`: Diagramas y relaciones de modelos
- `README.md`: Quick start y comandos principales
