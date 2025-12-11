# Modelado y proyección inicial para flota CSR

## Modelos principales

### `MaintenanceProfile`
Define cada ciclo de mantenimiento con disparador dual (kilómetros o tiempo). Incluye:
- `code` (elección restringida a IQ, B, A, BI, P, DE) y `name` para identificar el ciclo.
- `maintenance_type` para diferenciar livianos y pesados.
- `km_interval` y `time_interval_days` para los límites que disparan la intervención.

### `FleetModule`
Representa los módulos indivisibles de la flota CSR (PK 01-86), con:
- `module_type` (Cuádrupla o Tripla).
- `in_service_date`.
- `total_accumulated_km`, actualizado automáticamente tras registrar odómetros.

### `MaintenanceEvent`
Registra la última intervención aplicada a un módulo para un perfil concreto (siguiendo la abreviatura normativa definida en el `MaintenanceProfile`). Guarda la fecha y el odómetro al momento del servicio.

### `OdometerLog`
Tabla transaccional de lecturas de odómetro por fecha. Calcula `daily_delta_km` al guardarse y actualiza el acumulado del módulo.

## Servicio de proyección
`ProjectionService` estima la próxima fecha de mantenimiento por módulo y perfil aplicando el disparador dual:
1. Fecha límite por tiempo: última intervención + ventana de días del perfil.
2. Fecha estimada por kilometraje: proyecta cuándo se alcanzará el km del ciclo usando un promedio diario configurable (ventana de 30 días por defecto).

La próxima intervención es la fecha más temprana entre los dos disparadores disponibles.
