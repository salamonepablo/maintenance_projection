# Actualización de grilla de proyección y mapeo de códigos

## Resumen
Se ajustó el servicio de grilla para reflejar los campos reales de los modelos y se definió un mapeo consistente entre códigos de intervención de la grilla y los perfiles de mantenimiento.

## Cambios principales
- **Campos de eventos y odómetro**: la grilla usa `fleet_module`, `profile.code`, `event_date` y `odometer_km` al consultar `MaintenanceEvent` y `OdometerLog`.
- **Identificador de módulo**: se reemplazó `module_number` por `id` en vistas, exportaciones y plantilla para mantener coherencia con `FleetModule`.
- **Mapeo de códigos decanuales**:
  - Grilla: `DA`
  - Perfil: `DE`

## Mapeo aplicado
```python
GRID_TO_PROFILE_CODE = {
    "DA": "DE",
    "P": "P",
    "BI": "BI",
    "A": "A",
}
```
