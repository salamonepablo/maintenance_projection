# Configuración de variables de entorno

Este proyecto usa variables de entorno para definir la configuración básica de Django.

## Plantilla `.env`

Copiá el archivo `.env.example` a `.env` y ajustá los valores según tu entorno:

```bash
cp .env.example .env
```

## Variables mínimas

- `DEBUG`: habilita modo desarrollo (`True`/`False`).
- `SECRET_KEY`: clave secreta de Django. Usá un valor seguro en producción.
- `DATABASE_URL`: URL de conexión a la base de datos.
- `ALLOWED_HOSTS`: hosts permitidos separados por comas.

## Ejemplo

```env
DEBUG=True
SECRET_KEY=changeme
DATABASE_URL=postgres://usuario:password@localhost:5432/maintenance_db
ALLOWED_HOSTS=localhost,127.0.0.1
```
