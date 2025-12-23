# 📐 Diagramas y Arquitectura - Sincronización Access → Django

Visualizaciones del sistema de sincronización.

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                     SISTEMA COMPLETO                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐       ┌──────────┐  │
│  │   Frontend   │◄───────►│    Access    │◄──────│   VPN    │  │
│  │  (.accde)    │  Visual │   Backend    │ Red   │  Trabajo │  │
│  │  Escritorio  │  Users  │   (.accdb)   │       │          │  │
│  └──────────────┘         └──────┬───────┘       └──────────┘  │
│                                  │                              │
│                                  │ pyodbc                       │
│                                  │ ReadOnly                     │
│                                  ▼                              │
│                    ┌─────────────────────────┐                 │
│                    │   AccessExtractor       │                 │
│                    │   - Conectar            │                 │
│                    │   - Filtrar CSR (M%)    │                 │
│                    │   - Mapear ciclos       │                 │
│                    │   - Extraer datos       │                 │
│                    └─────────┬───────────────┘                 │
│                              │                                  │
│                              │ Python Objects                   │
│                              ▼                                  │
│                    ┌─────────────────────────┐                 │
│                    │  Django Management      │                 │
│                    │  sync_from_access.py    │                 │
│                    │  - Validar datos        │                 │
│                    │  - Transacciones        │                 │
│                    │  - get_or_create        │                 │
│                    └─────────┬───────────────┘                 │
│                              │                                  │
│                              │ Django ORM                       │
│                              ▼                                  │
│                    ┌─────────────────────────┐                 │
│                    │   Django PostgreSQL     │                 │
│                    │   - FleetModule         │                 │
│                    │   - MaintenanceEvent    │                 │
│                    │   - OdometerLog         │                 │
│                    └─────────┬───────────────┘                 │
│                              │                                  │
│                              │ Proyecciones                     │
│                              ▼                                  │
│                    ┌─────────────────────────┐                 │
│                    │   Dashboard Web         │                 │
│                    │   - Módulos M01-M86     │                 │
│                    │   - Proyecciones        │                 │
│                    │   - Alertas             │                 │
│                    └─────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Sincronización Detallado

```
INICIO
  │
  ├─[1] Validar Configuración
  │    ├─ ACCESS_CONNECTION_STRING existe?
  │    ├─ VPN conectada?
  │    └─ Ruta Access válida?
  │
  ├─[2] Conectar a Access
  │    ├─ pyodbc.connect(ReadOnly=1)
  │    ├─ Validar contraseña (0733)
  │    └─ Test de conexión
  │
  ├─[3] SINCRONIZAR MÓDULOS
  │    │
  │    ├─ Extraer de Access:
  │    │   ├─ SELECT DISTINCT Módulo FROM A_00_Kilometrajes
  │    │   │  WHERE Módulo LIKE 'M%'
  │    │   │
  │    │   └─ SELECT DISTINCT Módulos FROM A_00_OT_Consulta
  │    │      WHERE Módulos LIKE 'M%'
  │    │
  │    ├─ Para cada módulo M##:
  │    │   ├─ Extraer número (M01 → 1)
  │    │   ├─ Determinar tipo (1-42: CUADRUPLA, 43-86: TRIPLA)
  │    │   └─ Buscar formación actual (12_CambioMódulos, última fecha)
  │    │
  │    └─ Django:
  │        └─ FleetModule.objects.update_or_create(
  │               module_number=num,
  │               defaults={'module_type': tipo, 'is_active': True}
  │           )
  │
  ├─[4] SINCRONIZAR EVENTOS
  │    │
  │    ├─ Extraer de Access:
  │    │   ├─ SELECT Módulos, Tarea, Km, [Fecha Fin]
  │    │   │  FROM A_00_OT_Consulta
  │    │   │  WHERE Módulos LIKE 'M%'
  │    │   │    AND [Fecha Fin] >= fecha_desde
  │    │   │
  │    │   └─ Ordenar por [Fecha Fin] DESC
  │    │
  │    ├─ Para cada evento:
  │    │   ├─ Extraer primeros 2 chars de Tarea (IQ, IB, AN, BA, RS)
  │    │   ├─ Mapear: IQ→IQ, IB→B, AN→A, BA→BI, RS→P
  │    │   ├─ Buscar FleetModule (module_number)
  │    │   └─ Buscar MaintenanceProfile (cycle_type)
  │    │
  │    └─ Django:
  │        └─ MaintenanceEvent.objects.get_or_create(
  │               module=module,
  │               profile=profile,
  │               event_date=fecha,
  │               defaults={'odometer_km': km}
  │           )
  │
  ├─[5] SINCRONIZAR LECTURAS
  │    │
  │    ├─ Extraer de Access:
  │    │   ├─ SELECT Módulo, Kilometraje, Fecha
  │    │   │  FROM A_00_Kilometrajes
  │    │   │  WHERE Módulo LIKE 'M%'
  │    │   │    AND Fecha >= fecha_desde
  │    │   │
  │    │   └─ Ordenar por Fecha DESC
  │    │
  │    ├─ Para cada lectura:
  │    │   └─ Buscar FleetModule (module_number)
  │    │
  │    └─ Django:
  │        └─ OdometerLog.objects.get_or_create(
  │               module=module,
  │               reading_date=fecha,
  │               defaults={'odometer_reading': km}
  │           )
  │        ├─ Auto-calcula: daily_delta_km
  │        └─ Auto-actualiza: FleetModule.total_accumulated_km
  │
  ├─[6] Cerrar Conexión
  │    └─ conn.close()
  │
  └─[7] Mostrar Resumen
       ├─ Módulos sincronizados: XX
       ├─ Eventos sincronizados: XXX
       └─ Lecturas sincronizadas: XXXX

FIN
```

---

## 🗺️ Mapeo de Datos

### Módulos CSR

```
Access                             Django
──────                             ──────
A_00_Kilometrajes.Módulo = 'M01'  ─┐
                                    ├─► FleetModule
A_00_OT_Consulta.Módulos = 'M01'  ─┘    ├─ module_number = 1
                                         ├─ module_type = 'CUADRUPLA'
12_CambioMódulos                         └─ is_active = True
 ├─ Formación = 'F120'
 └─ Cabina = 'A'
```

### Eventos de Mantenimiento

```
Access                             Django
──────                             ──────
A_00_OT_Consulta                   MaintenanceEvent
 ├─ Módulos = 'M01'         ─────► ├─ module = FK(FleetModule #1)
 ├─ Tarea = 'IQ'            ─┐     ├─ profile = FK(MaintenanceProfile 'IQ')
 │   (primeros 2 chars)      │     ├─ event_date = 2025-12-19
 │                           │     └─ odometer_km = 1250000
 └─ Mapeo:                   │
     IQ → IQ  ───────────────┘
     IB → B
     AN → A
     BA → BI
     RS → P
```

### Lecturas de Odómetro

```
Access                             Django
──────                             ──────
A_00_Kilometrajes                  OdometerLog
 ├─ Módulo = 'M01'          ─────► ├─ module = FK(FleetModule #1)
 ├─ Kilometraje = 1250000          ├─ reading_date = 2025-12-19
 └─ Fecha = 2025-12-19             ├─ odometer_reading = 1250000
                                   ├─ daily_delta_km (auto)
                                   └─ Actualiza FleetModule.total_accumulated_km
```

---

## 🎯 Casos de Uso Visualizados

### Caso 1: Primera Sincronización (Setup)

```
Usuario                 Sistema                      Access          Django
  │                       │                           │               │
  ├─ sync --full ────────►│                           │               │
  │                       ├─ Conectar ───────────────►│               │
  │                       │◄─ OK (M01-M86, eventos) ─┤               │
  │                       │                           │               │
  │                       ├─ Crear 86 módulos ───────┼──────────────►│
  │                       │                           │   FleetModule │
  │                       │                           │   (86 rows)   │
  │                       │                           │               │
  │                       ├─ Insertar ~1000 eventos ─┼──────────────►│
  │                       │                           │   MaintenanceEvent
  │                       │                           │   (1000 rows) │
  │                       │                           │               │
  │                       ├─ Insertar ~5000 lecturas ┼──────────────►│
  │                       │                           │   OdometerLog │
  │                       │                           │   (5000 rows) │
  │◄─ Resumen completo ──┤                           │               │
  │   86 módulos          │                           │               │
  │   1000 eventos        │                           │               │
  │   5000 lecturas       │                           │               │
```

### Caso 2: Sincronización Diaria (Incremental)

```
Usuario                 Sistema                      Access          Django
  │                       │                           │               │
  ├─ sync ────────────────►│                           │               │
  │                       ├─ Conectar ───────────────►│               │
  │                       │                           │               │
  │                       ├─ Eventos últimos 30 días ►│               │
  │                       │◄─ 25 eventos nuevos ──────┤               │
  │                       │                           │               │
  │                       ├─ Lecturas últimos 7 días ►│               │
  │                       │◄─ 150 lecturas nuevas ────┤               │
  │                       │                           │               │
  │                       ├─ Insertar 25 eventos ─────┼──────────────►│
  │                       │                           │               │
  │                       ├─ Insertar 150 lecturas ───┼──────────────►│
  │◄─ Resumen ────────────┤                           │               │
  │   25 eventos          │                           │               │
  │   150 lecturas        │                           │               │
  │   Duración: 15 seg    │                           │               │
```

### Caso 3: Solo Lecturas (Post-Toma)

```
Técnico                 Sistema                      Access          Django
  │                       │                           │               │
  ├─ Toma lecturas ───────┼──────────────────────────►│               │
  │   en Access           │                           │  A_00_Kilometrajes
  │                       │                           │  + 86 filas   │
  │                       │                           │               │
Usuario                   │                           │               │
  ├─ sync --readings-only ►│                           │               │
  │                       ├─ Conectar ───────────────►│               │
  │                       │◄─ 86 lecturas de hoy ────┤               │
  │                       │                           │               │
  │                       ├─ Insertar 86 lecturas ────┼──────────────►│
  │                       │                           │   OdometerLog │
  │                       │                           │   Auto-calcula
  │                       │                           │   delta_km    │
  │◄─ OK: 86 lecturas ────┤                           │               │
```

---

## 🔐 Seguridad y Validaciones

```
┌─────────────────────────────────────────────────────────────┐
│                    VALIDACIONES APLICADAS                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [1] CONEXIÓN                                              │
│      ├─ ReadOnly = 1 (no modifica Access)                 │
│      ├─ Contraseña validada                               │
│      └─ Test de conectividad                              │
│                                                             │
│  [2] FILTROS                                               │
│      ├─ Solo CSR: Módulo LIKE 'M%'                        │
│      ├─ Excluir Toshiba: NOT LIKE 'T%'                    │
│      ├─ Excluir NULL en fechas                            │
│      └─ Excluir NULL en kilometrajes                      │
│                                                             │
│  [3] MAPEO DE CICLOS                                       │
│      ├─ Validar primeros 2 chars de Tarea                 │
│      ├─ Solo ciclos conocidos (IQ/IB/AN/BA/RS)            │
│      └─ Saltar tareas no reconocidas                      │
│                                                             │
│  [4] REFERENCIAS (FK)                                      │
│      ├─ Módulo existe en Django?                          │
│      ├─ Perfil existe en Django?                          │
│      └─ Saltar si FK no existe                            │
│                                                             │
│  [5] DUPLICADOS                                            │
│      ├─ get_or_create (no inserta duplicados)             │
│      ├─ Unique constraints respetados                     │
│      └─ update en caso de cambios                         │
│                                                             │
│  [6] TRANSACCIONES                                         │
│      ├─ transaction.atomic()                              │
│      ├─ Rollback automático en error                      │
│      └─ Todo o nada (no corrupción parcial)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Estructura de Módulos CSR

```
Módulo M01 (Ejemplo)
├─────────────────────────────────────────────────────┐
│                                                     │
│  Remolque 1 (R1)                                    │
│  └─ Coche: 5601                                     │
│     └─ Número módulo: XX01 → Módulo 01             │
│                                                     │
│  Remolque 2 (R2)                                    │
│  └─ Coche: 5801                                     │
│     └─ Número: 58XX → XX = 01                      │
│                                                     │
│  Motriz Cabecera (MC1)                             │
│  └─ Coche: 5001                                     │
│     └─ Cálculo: (01 * 2) - 1 = 1 → 5001           │
│                                                     │
│  Motriz Intermedio (MC2)                           │
│  └─ Coche: 5002                                     │
│     └─ Cálculo: 01 * 2 = 2 → 5002                 │
│                                                     │
│  Formación Actual: F120                             │
│  Cabina: A                                          │
│  Tipo: CUADRUPLA (módulos 1-42)                    │
│                                                     │
└─────────────────────────────────────────────────────┘

Fórmulas de Coches CSR:
  R1 (Remolque 1):    56 + XX
  R2 (Remolque 2):    58 + XX
  MC1 (Motriz 1):     50 + (XX * 2 - 1)
  MC2 (Motriz 2):     50 + (XX * 2)

Donde XX = número de módulo (01-86)
```

---

## 🎨 Estados del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                   ESTADOS DE SINCRONIZACIÓN                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [INITIAL] Sistema sin datos                               │
│      ↓                                                      │
│      sync --full                                            │
│      ↓                                                      │
│  [SYNCED] Datos completos en Django                        │
│      │                                                      │
│      ├─ Diario: sync                                       │
│      │    ↓                                                 │
│      │  [UP_TO_DATE] Datos actualizados                    │
│      │                                                      │
│      ├─ Lectura nueva en Access                            │
│      │    ↓                                                 │
│      │  [PENDING] Datos desactualizados                    │
│      │    ↓                                                 │
│      │    sync --readings-only                             │
│      │    ↓                                                 │
│      └──►[UP_TO_DATE]                                      │
│                                                             │
│  [ERROR] Fallo en sincronización                           │
│      ├─ Rollback automático                                │
│      └─ Django intacto (no corrupción)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Performance y Escalabilidad

```
Tamaño Actual:
├─ Módulos: ~86
├─ Eventos históricos: ~1,000
├─ Lecturas históricas: ~5,000
└─ Crecimiento mensual: ~50 eventos, ~200 lecturas

┌─────────────────────────────────────────────────────────────┐
│                    TIEMPOS DE EJECUCIÓN                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Operación           │ Registros │ Tiempo    │ Red         │
│  ────────────────────┼───────────┼───────────┼─────────────│
│  Full sync           │ ~6,086    │ 3-5 min   │ VPN         │
│  Incremental (día)   │ ~250      │ 15-30 seg │ VPN         │
│  Modules only        │ ~86       │ 5-10 seg  │ VPN         │
│  Events only         │ ~1,000    │ 1-2 min   │ VPN         │
│  Readings only       │ ~5,000    │ 2-3 min   │ VPN         │
│                                                             │
│  Proyecciones en                                            │
│  Dashboard           │ ~86       │ <1 seg    │ Local (PG)  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Optimizaciones:
├─ Usar --since para limitar rango
├─ Sincronizar en horarios de baja carga
├─ Ejecutar solo lo necesario (--xxx-only)
└─ Índices en BD (module_number, event_date)
```

---

**Arquitectura diseñada para:** ✅ Robustez ✅ Performance ✅ Mantenibilidad
