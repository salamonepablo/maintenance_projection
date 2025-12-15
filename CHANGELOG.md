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

## [0.3.0] - 2025-12-11
### Añadido
- Management command `import_legacy_data` para importar datos históricos desde CSVs (módulos, eventos de mantenimiento y lecturas de odómetro).
- Dependencias `pandas` y `tqdm` en `requirements.txt` para procesamiento ETL con barras de progreso.
- Soporte para parseo de formatos numéricos legacy con separadores de miles y coma decimal.
- Lógica automática de determinación de tipo de módulo (Cuádrupla/Tripla) basada en ID.
- Mapeo de códigos de mantenimiento legacy (IQ, B, A, BI, P, DE) a perfiles del sistema.

## [0.3.1] - 2025-12-11
### Añadido
- Suite completa de tests unitarios en `maintenance/tests/` para validar importación ETL y modelos.
- Tests de integración para flujo completo de importación (módulos → eventos → lecturas).
- Tests para `ProjectionService` validando proyecciones por tiempo y kilometraje.
- Archivo `.github/copilot-instructions.md` con guía para agentes de IA sobre arquitectura, patrones y workflows del proyecto.
- README actualizado con secciones de instalación, uso del ETL, estructura del proyecto y comandos de testing.

## [0.4.0] - 2025-12-15
### Añadido
- Configuración de `core/settings.py` con `django-environ` para lectura de `.env` y soporte PostgreSQL/SQLite.
- Archivo `.env.example` con template de configuración documentado.
- Django Admin completamente configurado en `maintenance/admin.py` con interfaces personalizadas para todos los modelos.
- Formateo de kilometrajes con separadores de miles en Admin.
- Coloreado de deltas anormales en lecturas de odómetro (Admin).
- Documentación completa de arquitectura de BD en `docs/database_architecture.md`.
- Estrategias de integración con sistema PHP/PostgreSQL de GTI (schemas compartidos, FDW, API REST).
- Configuración de timezone `America/Argentina/Buenos_Aires` y locale `es-ar`.
- App `maintenance` agregada a `INSTALLED_APPS`.

### Modificado
- README con sección de base de datos y opciones SQLite vs PostgreSQL.
