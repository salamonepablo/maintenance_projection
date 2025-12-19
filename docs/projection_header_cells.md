# Encabezado de proyección mensual

## Objetivo

Evitar el uso de `{% break %}` en el template `maintenance/templates/maintenance/projection.html`, ya que Django no soporta ese tag por defecto, y asegurar que el encabezado de meses se tome del primer módulo/primera fila disponibles.

## Implementación

- Se obtiene el primer módulo con `|first` y, a partir de él, la primera fila.
- Se recorren las celdas de esa fila para renderizar el encabezado de meses.
- Si no hay módulos o filas, el encabezado queda vacío sin generar errores.

## Archivo afectado

- `maintenance/templates/maintenance/projection.html`
