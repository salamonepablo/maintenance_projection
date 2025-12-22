<#
.SYNOPSIS
    Test rápido de conexión a Access
    
.PARAMETER AccessPath
    Ruta al archivo Access
    
.EXAMPLE
    .\Test-Connection.ps1 -AccessPath "C:\Data\flota.accdb"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$AccessPath
)

Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  Test Conexión Access v1.0.0  ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

if (-not (Test-Path $AccessPath)) {
    Write-Host "✗ No existe: $AccessPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "test_connection.py")) {
    Write-Host "✗ No se encuentra test_connection.py" -ForegroundColor Red
    Write-Host "   Cópialo al directorio actual" -ForegroundColor Yellow
    exit 1
}

python test_connection.py "$AccessPath"
$exitCode = $LASTEXITCODE

Write-Host ""

if ($exitCode -eq 0) {
    Write-Host "✓ Conexión OK - Puedes continuar con exploración completa" -ForegroundColor Green
} else {
    Write-Host "✗ Revisa los errores arriba" -ForegroundColor Red
}

Write-Host ""
exit $exitCode
