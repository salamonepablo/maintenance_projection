# Exportación de proyección

## Objetivo

Actualizar el acceso a la exportación de proyección para utilizar la ruta dedicada y mantener compatibilidad con enlaces antiguos.

## Cambios

- El botón "Exportar a Excel" ahora apunta a la URL `maintenance:projection_export` preservando los parámetros `months` y `monthly_km`.
- La vista `projection_view` acepta `export=excel` como compatibilidad, delegando internamente en `projection_export_excel`.
