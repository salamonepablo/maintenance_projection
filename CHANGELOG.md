# Changelog

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto sigue [Versionado Semántico](https://semver.org/lang/es/).

## [0.1.0] - 2024-12-11
### Añadido
- Modelos iniciales de Django para módulos de flota, perfiles y eventos de mantenimiento, y registros de odómetro.
- Servicio `ProjectionService` para estimar próximas intervenciones con disparador dual.
- Documentación en `docs/maintenance_models.md` describiendo los modelos y la lógica de proyección.

## [0.1.1] - 2024-12-12
### Añadido
- Restricción de abreviaturas normativas para los perfiles de mantenimiento (IQ, B, A, BI, P, DE) usada por los eventos.
- Actualización de la documentación de modelos para reflejar las abreviaturas y su uso en los eventos.

## [0.2.0] - 2025-12-10
### Añadido
- Archivo de dependencias `requirements.txt` con Django, psycopg, python-dotenv y django-environ.
- Guía de configuración inicial en `docs/setup.md` para Windows (PowerShell), incluyendo venv, configuración de `DATABASE_URL`, migraciones y ejecución del servidor.

## [0.2.1] - 2025-12-11
### Añadido
- Archivo `.gitignore` con reglas para Python/Django, entornos virtuales, archivos temporales, bases de datos locales, cobertura y configuraciones de IDE.
