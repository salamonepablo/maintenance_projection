# Install-AccessSync.ps1
# Script de instalación automática del sistema de sincronización Access → Django

[CmdletBinding()]
param(
    [string]$ProjectPath = "C:\Programmes\maintenance_projection",
    [switch]$SkipDependencies
)

$ErrorActionPreference = "Stop"

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  INSTALADOR - Sincronización Access → Django                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Validar ruta del proyecto
Write-Host "→ Validando proyecto Django..." -ForegroundColor Yellow
if (-not (Test-Path "$ProjectPath\manage.py")) {
    Write-Host "✗ No se encuentra manage.py en: $ProjectPath" -ForegroundColor Red
    Write-Host "  Use: -ProjectPath 'C:\ruta\a\tu\proyecto'" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Proyecto encontrado" -ForegroundColor Green

# 2. Verificar entorno virtual
Write-Host "→ Verificando entorno virtual..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectPath ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "✗ No se encuentra .venv en: $venvPath" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Entorno virtual encontrado" -ForegroundColor Green

# 3. Activar entorno virtual
Write-Host "→ Activando entorno virtual..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

# 4. Verificar/Instalar pyodbc
if (-not $SkipDependencies) {
    Write-Host "→ Verificando pyodbc..." -ForegroundColor Yellow
    $pyodbcInstalled = python -c "import pyodbc; print('OK')" 2>$null
    
    if ($pyodbcInstalled -ne "OK") {
        Write-Host "  Instalando pyodbc..." -ForegroundColor Yellow
        pip install pyodbc
        Write-Host "✓ pyodbc instalado" -ForegroundColor Green
    } else {
        Write-Host "✓ pyodbc ya instalado" -ForegroundColor Green
    }
}

# 5. Crear carpetas necesarias
Write-Host "→ Creando estructura de carpetas..." -ForegroundColor Yellow

$servicesPath = Join-Path $ProjectPath "maintenance\services"
$commandsPath = Join-Path $ProjectPath "maintenance\management\commands"

New-Item -Path $servicesPath -ItemType Directory -Force | Out-Null
New-Item -Path $commandsPath -ItemType Directory -Force | Out-Null

Write-Host "✓ Carpetas creadas" -ForegroundColor Green

# 6. Copiar archivos
Write-Host "→ Copiando archivos..." -ForegroundColor Yellow

$currentPath = $PSScriptRoot

# Copiar extractor
$extractorSrc = Join-Path $currentPath "access_extractor.py"
$extractorDst = Join-Path $servicesPath "access_extractor.py"
Copy-Item $extractorSrc $extractorDst -Force
Write-Host "  ✓ access_extractor.py" -ForegroundColor Green

# Copiar comando
$commandSrc = Join-Path $currentPath "sync_from_access.py"
$commandDst = Join-Path $commandsPath "sync_from_access.py"
Copy-Item $commandSrc $commandDst -Force
Write-Host "  ✓ sync_from_access.py" -ForegroundColor Green

# Crear __init__.py en commands
$initFile = Join-Path $commandsPath "__init__.py"
if (-not (Test-Path $initFile)) {
    "# Django management commands" | Out-File $initFile -Encoding UTF8
    Write-Host "  ✓ __init__.py creado" -ForegroundColor Green
}

# 7. Mostrar configuración
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  CONFIGURAR SETTINGS.PY                                      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Agregar al final de settings.py:" -ForegroundColor Yellow
Write-Host ""
Write-Host @"
# ==============================================================================
# CONFIGURACIÓN DE SINCRONIZACIÓN CON ACCESS
# ==============================================================================

ACCESS_DATABASE_PATH = r'G:\Material Rodante\1-Servicio Eléctrico\DB\Base de Datos Mantenimiento\DB_CCEE_Mantenimiento 1.0.accdb'
ACCESS_DATABASE_PASSWORD = '0733'

ACCESS_CONNECTION_STRING = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={ACCESS_DATABASE_PATH};'
    f'PWD={ACCESS_DATABASE_PASSWORD};'
    'ReadOnly=1;'
)

# ==============================================================================
"@ -ForegroundColor White

Write-Host ""
Write-Host "Archivo: $ProjectPath\core\settings.py" -ForegroundColor Gray
Write-Host ""

# 8. Instrucciones finales
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PRÓXIMOS PASOS                                              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Agregar configuración a settings.py (ver arriba)" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Crear perfiles de mantenimiento:" -ForegroundColor Yellow
Write-Host "   python manage.py shell" -ForegroundColor White
Write-Host "   # Ejecutar código de creación de perfiles (ver INSTALACION.md)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Probar conexión:" -ForegroundColor Yellow
Write-Host "   python manage.py sync_from_access --test" -ForegroundColor White
Write-Host ""
Write-Host "4. Primera sincronización:" -ForegroundColor Yellow
Write-Host "   python manage.py sync_from_access --full" -ForegroundColor White
Write-Host ""
Write-Host "Ver: INSTALACION.md para detalles completos" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Instalación completada exitosamente" -ForegroundColor Green
Write-Host ""
