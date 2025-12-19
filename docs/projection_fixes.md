# Ajustes de proyección y exportación

## Resumen

Se corrigió la capa de proyección para alinearla con los modelos reales del sistema y evitar errores en runtime. Además, se mejoró la plantilla HTML y se agregó la dependencia necesaria para exportación Excel.

## Cambios principales

- **Servicios de proyección**: se alinearon campos con `FleetModule`, `MaintenanceEvent` y `OdometerLog` (por ejemplo `fleet_module`, `event_date`, `odometer_km`).
- **Mapeo de códigos**: la proyección mantiene el código visual `DA` y lo mapea al código de perfil `DE`.
- **Vistas**: se eliminó duplicación y se corrigieron filtros por `id` del módulo.
- **Template**: se eliminó `{% break %}` y se agregó `header_months` desde la vista. El enlace de exportación apunta al endpoint real.
- **Dependencias**: se añadió `openpyxl` para la exportación a Excel.
- **Configuración**: se agregó `.env.example` para facilitar el setup.

## Archivos impactados

- `maintenance/services/projection_grid.py`
- `maintenance/views.py`
- `maintenance/templates/maintenance/projection.html`
- `requirements.txt`
- `.env.example`
