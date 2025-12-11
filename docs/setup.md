# Configuración del entorno (Windows)

Esta guía te permite levantar el entorno de desarrollo con Django y PostgreSQL.

## Prerrequisitos
- Python 3.11+ instalado y en PATH
- PostgreSQL 14+ con un usuario y base creados
- PowerShell 5.1 (por defecto en Windows)

## Crear y activar entorno virtual
```powershell
# En la raíz del proyecto
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## Instalar dependencias
```powershell
pip install -r requirements.txt
```

Dependencias clave:
- Django: framework web.
- psycopg[binary]: conector PostgreSQL.
- python-dotenv / django-environ: manejo de variables de entorno.

## Configurar variables de entorno
Define la conexión a PostgreSQL con `DATABASE_URL` (formato RFC):
```powershell
$env:DATABASE_URL = "postgres://usuario:password@localhost:5432/maintenance_db"
```
Opcionalmente, puedes crear un archivo `.env` en la raíz:
```
DATABASE_URL=postgres://usuario:password@localhost:5432/maintenance_db
DEBUG=true
SECRET_KEY=changeme_dev_secret
```

## Inicializar proyecto Django (si aún no existe)
Si ya tienes `manage.py` y una configuración de Django, omite este paso.
```powershell
# Crea un proyecto llamado core y una app llamada maintenance
python -m django startproject core .
python manage.py startapp maintenance
```

Añade `maintenance` a `INSTALLED_APPS` en `core/settings.py` y configura la base de datos usando `django-environ` o `python-dotenv`.

Ejemplo mínimo usando `django-environ`:
```python
# core/settings.py
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
# lee .env si existe
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='changeme_dev_secret')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'maintenance',
]
```

## Migraciones y superusuario
```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Ejecutar servidor de desarrollo
```powershell
python manage.py runserver
```

## Próximos pasos
- Cargar datos de `FleetModule` y `OdometerLog`.
- Definir vistas y admin para gestionar `MaintenanceProfile` y `MaintenanceEvent`.
- Añadir comandos de importación de lecturas (Excel/PDF/Texto) según fuentes.
