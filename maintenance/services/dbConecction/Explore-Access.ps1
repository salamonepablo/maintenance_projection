<#
.SYNOPSIS
    Explora base de datos Access
    
.DESCRIPTION
    Conecta a Access y genera reporte completo con todas las tablas,
    consultas, estructura y datos de ejemplo.
    
.PARAMETER AccessPath
    Ruta al archivo Access (.mdb o .accdb)
    
.PARAMETER OutputPath
    Ruta donde guardar el reporte (opcional)
    
.EXAMPLE
    .\Explore-Access.ps1 -AccessPath "C:\Data\flota.accdb"
    
.EXAMPLE
    .\Explore-Access.ps1 -AccessPath "C:\Data\flota.accdb" -OutputPath "C:\Reports\reporte.txt"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$AccessPath,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "access_report.txt"
)

$ErrorActionPreference = "Stop"

function Write-Step { param([string]$msg) Write-Host "`n→ $msg" -ForegroundColor Cyan }
function Write-Success { param([string]$msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error { param([string]$msg) Write-Host "✗ $msg" -ForegroundColor Red }

# Banner
Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  Explorador de Base de Datos Access   ║" -ForegroundColor Blue
Write-Host "║              v1.0.0                    ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Verificar Access
if (-not (Test-Path $AccessPath)) {
    Write-Error "No se encuentra el archivo: $AccessPath"
    exit 1
}

Write-Success "Archivo Access encontrado"
Write-Host "   Ruta: $AccessPath"
Write-Host ""

# Verificar pyodbc
Write-Step "Verificando dependencias..."

try {
    $pyodbcTest = python -c "import pyodbc; print('OK')" 2>&1
    
    if ($pyodbcTest -match "OK") {
        Write-Success "pyodbc instalado"
    } else {
        Write-Host "⚠ pyodbc no encontrado, instalando..." -ForegroundColor Yellow
        pip install pyodbc --quiet
        Write-Success "pyodbc instalado"
    }
} catch {
    Write-Error "Error verificando pyodbc: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Instala pyodbc manualmente:" -ForegroundColor Yellow
    Write-Host "   pip install pyodbc" -ForegroundColor Cyan
    exit 1
}

# Verificar driver de Access
Write-Step "Verificando driver de Access..."

$drivers = [System.Data.Odbc.OdbcConnection]::GetDataSources([System.Data.Odbc.OdbcSourceType]::System)
$hasAccessDriver = $false

# Verificar si existe el driver de Access
try {
    $odbcDrivers = Get-OdbcDriver | Where-Object { $_.Name -like "*Access*" }
    if ($odbcDrivers) {
        Write-Success "Driver de Access encontrado: $($odbcDrivers[0].Name)"
        $hasAccessDriver = $true
    }
} catch {
    # Intentar de otra forma
    try {
        $testConnection = [System.Data.Odbc.OdbcConnection]::new()
        $testConnection.ConnectionString = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=$AccessPath;"
        $testConnection.Open()
        $testConnection.Close()
        Write-Success "Driver de Access encontrado"
        $hasAccessDriver = $true
    } catch {
        # No se pudo verificar
    }
}

if (-not $hasAccessDriver) {
    Write-Host "⚠ No se pudo verificar el driver de Access" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Si ves errores de conexión, descarga e instala:" -ForegroundColor Yellow
    Write-Host "Microsoft Access Database Engine 2016 Redistributable" -ForegroundColor Cyan
    Write-Host "https://www.microsoft.com/download/details.aspx?id=54920" -ForegroundColor Cyan
    Write-Host ""
    
    $continue = Read-Host "¿Continuar de todos modos? (S/n)"
    if ($continue -eq 'n' -or $continue -eq 'N') {
        exit 0
    }
}

# Crear script temporal si no existe
$scriptPath = "explore_access.py"
if (-not (Test-Path $scriptPath)) {
    Write-Host "⚠ Script explore_access.py no encontrado en el directorio actual" -ForegroundColor Yellow
    Write-Host "   Búscalo en el paquete descargado y cópialo aquí" -ForegroundColor Yellow
    exit 1
}

# Ejecutar explorador
Write-Step "Conectando a Access y generando reporte..."
Write-Host ""

try {
    # Ejecutar script Python
    $output = python $scriptPath "$AccessPath" 2>&1
    
    # Mostrar output
    $output | ForEach-Object {
        Write-Host $_
    }
    
    # Verificar si se generó el reporte
    if (Test-Path $OutputPath) {
        Write-Host ""
        Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║   ✓ Exploración Completada            ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        
        # Estadísticas del reporte
        $reportContent = Get-Content $OutputPath -Raw
        $lines = $reportContent -split "`n"
        
        Write-Host "📊 Resumen del Reporte:" -ForegroundColor Yellow
        Write-Host "   Archivo: $AccessPath"
        Write-Host "   Reporte: $OutputPath"
        Write-Host "   Líneas: $($lines.Count)"
        Write-Host ""
        
        # Extraer info clave
        $tablesLine = $lines | Where-Object { $_ -match "Tablas encontradas:" }
        $queriesLine = $lines | Where-Object { $_ -match "Consultas encontradas:" }
        
        if ($tablesLine) {
            Write-Host "   $($tablesLine.Trim())"
        }
        if ($queriesLine) {
            Write-Host "   $($queriesLine.Trim())"
        }
        
        Write-Host ""
        Write-Host "Próximos pasos:" -ForegroundColor Cyan
        Write-Host "1. Abre el reporte: notepad $OutputPath" -ForegroundColor White
        Write-Host "2. Revisa las tablas y consultas disponibles" -ForegroundColor White
        Write-Host "3. Identifica cuáles tienen los datos de módulos/mantenimiento" -ForegroundColor White
        Write-Host "4. Comparte capturas de pantalla para adaptar el código" -ForegroundColor White
        Write-Host ""
        
        # Preguntar si abrir reporte
        $open = Read-Host "¿Abrir reporte ahora? (S/n)"
        
        if ($open -ne 'n' -and $open -ne 'N') {
            notepad $OutputPath
        }
        
    } else {
        Write-Error "No se generó el reporte"
        exit 1
    }
    
} catch {
    Write-Error "Error durante exploración: $($_.Exception.Message)"
    exit 1
}

Write-Host ""
