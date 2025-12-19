# Vistas de proyección de mantenimiento

## Fuente oficial de las vistas

La implementación oficial de las vistas de proyección vive en
`maintenance/views_projection.py`. El módulo `maintenance/views.py` actúa como
fachada pública y reexporta las funciones para evitar duplicación de lógica y
mantener un único punto de mantenimiento.

## Vistas disponibles

- `projection_view`: renderiza la grilla HTML de proyección.
- `projection_export_excel`: exporta la proyección a Excel.
- `projection_api`: expone la proyección en formato JSON.
