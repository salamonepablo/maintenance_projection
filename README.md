# Maintenance Projection - Material Rodante Argentino

Sistema de proyección de mantenimiento ferroviario para la flota CSR (Coches Semi-Remolcados) de trenes argentinos.

## 📋 Descripción

Aplicación Django que gestiona el ciclo completo de mantenimiento preventivo de módulos ferroviarios mediante:
- **Disparador dual**: Proyecciones por tiempo transcurrido y kilometraje acumulado
- **Perfiles configurables**: Quincenal (IQ), Bimestral (B), Anual (A), Bianual (BI), Pentanual (P), Decanual (DE)
- **Historial completo**: Eventos de mantenimiento y lecturas de odómetro
- **ETL integrado**: Importación de datos legacy desde CSV

## 🚀 Instalación

### Prerrequisitos
- Python 3.11+
- PostgreSQL 14+ (recomendado) o SQLite
- Git

### Setup rápido (Windows)

```powershell
# Clonar repositorio
git clone https://github.com/salamonepablo/maintenance_projection.git
cd maintenance_projection

# Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# Configurar base de datos
# Opción 1: Copiar .env.example y ajustar (recomendado)
Copy-Item .env.example .env
# Editar .env con tus credenciales

# Opción 2: Variable de entorno directa
$env:DATABASE_URL = "postgres://usuario:password@localhost:5432/maintenance_db"

# Para desarrollo rápido: omitir DATABASE_URL usa SQLite por defecto

# Aplicar migraciones
python manage.py makemigrations maintenance
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

Ver [docs/setup.md](docs/setup.md) para instrucciones detalladas de configuración.

## 📊 Importación de Datos Legacy

Para poblar la base con datos históricos desde archivos CSV:

```powershell
# Importación completa (módulos + eventos + lecturas)
python manage.py import_legacy_data

# Con rutas personalizadas
python manage.py import_legacy_data \
    --modulos ruta/CSR_Modulos.csv \
    --eventos ruta/CSR_MantEvents.csv \
    --lecturas ruta/CSR_LecturasKms.csv

# Opciones útiles
python manage.py import_legacy_data --clear      # Borra datos previos
python manage.py import_legacy_data --skip-eventos  # Omite eventos
python manage.py import_legacy_data --help       # Ver todas las opciones
```

**Formato de archivos esperado:**

| Archivo | Columnas requeridas |
|---------|---------------------|
| `CSR_Modulos.csv` | FORMACION, MODULO, MC1, R1, R2, MC2 |
| `CSR_MantEvents.csv` | Id_Mantenimiento, Módulo, Tipo_Mantenimiento, Fecha, Kilometraje |
| `CSR_LecturasKms.csv` | Id_Kilometrajes, Módulo, kilometraje, Fecha |

Ver ejemplos en `context/`.

## 🧪 Tests

```powershell
# Ejecutar tests unitarios
python manage.py test maintenance

# Con cobertura
pip install coverage
coverage run --source='.' manage.py test maintenance
coverage report
```

## 🏃 Ejecución

```powershell
# Servidor de desarrollo
python manage.py runserver

# Acceder al admin en http://localhost:8000/admin
# Usuario/contraseña: los que creaste con createsuperuser
```

## 🗄️ Base de Datos

### Desarrollo Local

**SQLite** (por defecto, sin configuración):
```powershell
# No definir DATABASE_URL en .env
python manage.py migrate
```

**PostgreSQL** (recomendado, igual a producción):
```powershell
# 1. Instalar PostgreSQL 14+
# 2. Crear base y usuario
createdb maintenance_db
createuser maintenance_user -P

# 3. Configurar en .env
# DATABASE_URL=postgres://maintenance_user:password@localhost:5432/maintenance_db

# 4. Migrar
python manage.py migrate
```

Ver [docs/database_architecture.md](docs/database_architecture.md) para:
- Estrategias de integración con sistema PHP/PostgreSQL de GTI
- Esquemas compartidos vs Foreign Data Wrappers
- Recomendaciones para presentación a gerencia

## 📁 Estructura del Proyecto

```
maintenance_projection/
├── .env.example         # Template de configuración (copiar a .env)
├── context/             # Archivos CSV de ejemplo y documentación de negocio
├── docs/                # Documentación técnica
│   ├── setup.md        # Guía de instalación
│   ├── maintenance_models.md  # Especificación de modelos
│   └── database_architecture.md  # Arquitectura BD y estrategia de integración
├── maintenance/         # App Django principal
│   ├── models.py       # Modelos de datos (FleetModule, MaintenanceEvent, etc.)
│   ├── admin.py        # Configuración Django Admin
│   ├── management/     # Comandos personalizados
│   │   └── commands/
│   │       └── import_legacy_data.py  # ETL de datos históricos
│   └── tests/          # Tests unitarios
├── core/               # Configuración Django
│   └── settings.py    # Settings con django-environ
├── requirements.txt    # Dependencias Python
└── manage.py          # CLI de Django
```

## 🛠 Tecnologías

- **Backend**: Django 5.0+, Python 3.11+
- **Base de datos**: PostgreSQL 14+ / SQLite
- **ETL**: pandas, tqdm
- **Testing**: unittest (Django)

## 📝 Licencia

MIT License. Ver [LICENSE](LICENSE) para detalles.

## 👤 Autor

Pablo Salamone - [salamonepablo](https://github.com/salamonepablo)
