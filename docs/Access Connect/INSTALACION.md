# 🚀 Guía de Instalación - Sincronización Access → Django

Sistema de sincronización automática entre Access y Django para proyección de mantenimiento ferroviario.

---

## 📋 Requisitos Previos

✅ Python 3.11+  
✅ Django funcionando (maintenance_projection)  
✅ pyodbc instalado: `pip install pyodbc`  
✅ Microsoft Access Database Engine instalado  
✅ Acceso VPN a la red del trabajo (para acceder al backend Access)

---

## 📂 Paso 1: Copiar Archivos

### 1.1 Copiar el Extractor

```powershell
# Copiar access_extractor.py a tu carpeta de servicios
Copy-Item access_extractor.py C:\Programmes\maintenance_projection\maintenance\services\
```

### 1.2 Copiar el Comando Django

```powershell
# Crear carpeta para comandos si no existe
New-Item -Path "C:\Programmes\maintenance_projection\maintenance\management\commands" -ItemType Directory -Force

# Copiar el comando
Copy-Item sync_from_access.py C:\Programmes\maintenance_projection\maintenance\management\commands\
```

**IMPORTANTE**: Asegurate que la carpeta `commands` tenga un `__init__.py`:

```powershell
# Crear __init__.py si no existe
New-Item -Path "C:\Programmes\maintenance_projection\maintenance\management\commands\__init__.py" -ItemType File -Force
```

---

## ⚙️ Paso 2: Configurar Django

### 2.1 Agregar Configuración a settings.py

Abrir `C:\Programmes\maintenance_projection\core\settings.py` y agregar al final:

```python
# ==============================================================================
# CONFIGURACIÓN DE SINCRONIZACIÓN CON ACCESS
# ==============================================================================

# Ruta al backend Access
ACCESS_DATABASE_PATH = r'G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb'

# Contraseña de Access
ACCESS_DATABASE_PASSWORD = '0733'

# Connection string completo
ACCESS_CONNECTION_STRING = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={ACCESS_DATABASE_PATH};'
    f'PWD={ACCESS_DATABASE_PASSWORD};'
    'ReadOnly=1;'
)
```

**Nota**: Si la ruta del Access cambia, solo modificar `ACCESS_DATABASE_PATH`.

---

## 🧪 Paso 3: Probar la Conexión

### 3.1 Test Básico

```powershell
cd C:\Programmes\maintenance_projection

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Probar conexión
python manage.py sync_from_access --test
```

**Salida esperada**:
```
Conectando a Access...
✓ Conexión exitosa
  Módulos CSR en Access: XX
  Eventos en Access: XXX
  Lecturas en Access: XXXX

MODO PRUEBA - No se modificará la BD
...
```

---

## 📊 Paso 4: Primera Sincronización

### 4.1 Crear Perfiles de Mantenimiento

**IMPORTANTE**: Antes de sincronizar eventos, crear los perfiles:

```powershell
python manage.py shell
```

```python
from maintenance.models import MaintenanceProfile

# Crear perfiles según ciclos CSR
profiles = [
    {'cycle_type': 'IQ', 'km_interval': 6250, 'time_interval_days': 15},
    {'cycle_type': 'B', 'km_interval': 25000, 'time_interval_days': 60},
    {'cycle_type': 'A', 'km_interval': 187500, 'time_interval_days': 456},  # ~15 meses
    {'cycle_type': 'BI', 'km_interval': 375000, 'time_interval_days': 912},  # ~2.5 años
    {'cycle_type': 'P', 'km_interval': 750000, 'time_interval_days': 1825},  # ~5 años
    {'cycle_type': 'DE', 'km_interval': 1500000, 'time_interval_days': 3650},  # ~10 años
]

for p in profiles:
    MaintenanceProfile.objects.get_or_create(**p)
    print(f"✓ Perfil {p['cycle_type']} creado")

exit()
```

### 4.2 Sincronizar Todo

```powershell
# Sincronización completa (primera vez)
python manage.py sync_from_access --full
```

Esto sincronizará:
- ✅ Todos los módulos CSR activos
- ✅ Todos los eventos de mantenimiento
- ✅ Todas las lecturas de odómetro

**Duración estimada**: 2-5 minutos dependiendo de la cantidad de datos.

---

## 🔄 Paso 5: Uso Cotidiano

### 5.1 Sincronización Incremental (Diaria)

```powershell
# Sincronizar solo datos nuevos/modificados
python manage.py sync_from_access
```

Por defecto sincroniza:
- Eventos de los últimos 30 días
- Lecturas de los últimos 7 días

### 5.2 Sincronización Parcial

```powershell
# Solo módulos
python manage.py sync_from_access --modules-only

# Solo eventos
python manage.py sync_from_access --events-only

# Solo lecturas
python manage.py sync_from_access --readings-only

# Desde fecha específica
python manage.py sync_from_access --since 2025-01-01
```

### 5.3 Modo Prueba

```powershell
# Ver qué se sincronizaría sin modificar nada
python manage.py sync_from_access --test
python manage.py sync_from_access --full --test
```

---

## ⏰ Paso 6: Automatizar Sincronización

### Opción A: Task Scheduler (Windows)

Crear script `sync_daily.ps1`:

```powershell
# sync_daily.ps1
Set-Location "C:\Programmes\maintenance_projection"
.\.venv\Scripts\Activate.ps1
python manage.py sync_from_access
```

Crear tarea en Task Scheduler:
1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Nombre: "Sync Access to Django"
4. Trigger: Diario a las 7:00 AM
5. Acción: Ejecutar `powershell.exe`
6. Argumentos: `-File "C:\path\to\sync_daily.ps1"`

### Opción B: Django Management Command en Startup

En `settings.py`:

```python
ACCESS_SYNC_CONFIG = {
    'AUTO_SYNC_ON_STARTUP': True,  # Sincroniza al iniciar servidor
}
```

---

## 📊 Verificar Sincronización

### En Django Admin

1. Ir a: `http://localhost:8000/admin`
2. Ver:
   - **Fleet Modules**: Debe haber ~86 módulos CSR
   - **Maintenance Events**: Eventos con tipos IQ, B, A, BI, P
   - **Odometer Logs**: Lecturas periódicas

### En el Dashboard

```powershell
python manage.py runserver
```

Ir a: `http://localhost:8000/maintenance/projection/`

Deberías ver:
- ✅ Módulos M01-M86
- ✅ Últimos mantenimientos por módulo
- ✅ Proyecciones calculadas
- ✅ Alertas de vencimientos

---

## 🔍 Mapeo de Datos

### Access → Django

**Ciclos de Mantenimiento**:
```
IQ (Access) → IQ (Django)  # Quincenal
IB (Access) → B (Django)   # Bimestral
AN (Access) → A (Django)   # Anual
BA (Access) → BI (Django)  # Bianual
RS (Access) → P (Django)   # Pentanual
#N/A        → DE (Django)  # Decanual (aún no en Access)
```

**Tablas Access**:
```
A_00_Kilometrajes  → OdometerLog (Lecturas)
A_00_OT_Consulta   → MaintenanceEvent (Eventos)
                   → FleetModule (Módulos CSR)
```

**Filtros Aplicados**:
- Solo módulos CSR: `Módulo LIKE 'M%'`
- Excluye Toshiba: `Módulo NOT LIKE 'T%'`

---

## 🐛 Troubleshooting

### Error: "No es una contraseña válida"

**Causa**: Contraseña incorrecta o archivo protegido  
**Solución**: Verificar `ACCESS_DATABASE_PASSWORD` en settings.py

### Error: "No se pudo conectar"

**Causa**: VPN desconectada o ruta incorrecta  
**Solución**:
1. Verificar VPN activa
2. Verificar ruta en `ACCESS_DATABASE_PATH`
3. Probar con: `Test-Path "G:\Material Rodante\..."`

### Error: "Módulo X no existe en BD"

**Causa**: Evento/lectura para módulo no sincronizado  
**Solución**:
```powershell
python manage.py sync_from_access --modules-only
```

### Error: "Perfil X no existe"

**Causa**: Falta crear perfiles de mantenimiento  
**Solución**: Ejecutar Paso 4.1 (crear perfiles)

---

## 📈 Performance

**Primera sincronización completa**:
- ~86 módulos
- ~500-1000 eventos
- ~2000-5000 lecturas
- Tiempo: 2-5 minutos

**Sincronización incremental diaria**:
- ~10-50 eventos nuevos
- ~100-200 lecturas nuevas
- Tiempo: 10-30 segundos

---

## 🔒 Seguridad

- ✅ Conexión en modo **ReadOnly** (no modifica Access)
- ✅ Contraseña almacenada en settings (no en código)
- ✅ Transacciones atómicas en Django
- ✅ Validación de datos antes de insertar

---

## 📞 Soporte

Si algo falla, compartir:
1. ✅ Comando ejecutado
2. ✅ Error completo
3. ✅ Salida de: `python manage.py sync_from_access --test`

---

## ✅ Checklist de Instalación

```
☐ pyodbc instalado
☐ Access Database Engine instalado
☐ VPN conectada
☐ Archivos copiados:
   ☐ access_extractor.py
   ☐ sync_from_access.py
☐ settings.py configurado
☐ Test de conexión exitoso
☐ Perfiles de mantenimiento creados
☐ Sincronización completa ejecutada
☐ Dashboard funcionando
```

---

**¡Listo para usar!** 🚀
