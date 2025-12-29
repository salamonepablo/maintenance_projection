<#
.SYNOPSIS
    Actualiza la configuración de proxy en todas las herramientas (Windows, Git, npm, pip, VS Code)
.DESCRIPTION
    Script para actualizar periódicamente la URL del proxy cuando cambia la clave o configuración
.PARAMETER ProxyUrl
    URL completa del proxy (ej: http://usuario:clave@host:puerto)
.EXAMPLE
    .\update_proxy.ps1
    # Modo interactivo - pide la URL
    
    .\update_proxy.ps1 -ProxyUrl "http://pablo.salamone:gdsk-121@172.22.10.121:80"
    # Modo directo con parámetro
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="URL del proxy (ej: http://usuario:clave@host:puerto)")]
    [string]$ProxyUrl
)

# Colores para output
$ErrorColor = 'Red'
$SuccessColor = 'Green'
$InfoColor = 'Cyan'

Write-Host "=" * 60 -ForegroundColor $InfoColor
Write-Host "ACTUALIZADOR DE PROXY MULTIHERRAMIENTA" -ForegroundColor $InfoColor
Write-Host "=" * 60

Write-Host "`nActualizando proxy a:" -ForegroundColor $InfoColor
Write-Host $ProxyUrl

# 1. Variables de entorno (sesión)
Write-Host "`n[1/6] Actualizando variables de entorno (sesión)..." -ForegroundColor $InfoColor
try {
    $env:HTTP_PROXY = $ProxyUrl
    $env:HTTPS_PROXY = $ProxyUrl
    $env:NO_PROXY = "localhost,127.0.0.1"
    Write-Host "✓ Sesión actualizada" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ Error en sesión: $_" -ForegroundColor $ErrorColor
}

# 2. Variables de entorno (usuario persistente)
Write-Host "`n[2/6] Guardando en variables de entorno de usuario (persistente)..." -ForegroundColor $InfoColor
try {
    [Environment]::SetEnvironmentVariable("HTTP_PROXY", $ProxyUrl, "User")
    [Environment]::SetEnvironmentVariable("HTTPS_PROXY", $ProxyUrl, "User")
    [Environment]::SetEnvironmentVariable("NO_PROXY", "localhost,127.0.0.1", "User")
    Write-Host "✓ Variables de usuario guardadas" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ Error al guardar variables de usuario: $_" -ForegroundColor $ErrorColor
}

# 3. Git
Write-Host "`n[3/6] Actualizando Git..." -ForegroundColor $InfoColor
try {
    git config --global http.proxy $ProxyUrl
    git config --global https.proxy $ProxyUrl
    $gitProxyCheck = git config --global --get http.proxy
    Write-Host "✓ Git configurado: $gitProxyCheck" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ Error en Git: $_" -ForegroundColor $ErrorColor
}

# 4. npm
Write-Host "`n[4/6] Actualizando npm..." -ForegroundColor $InfoColor
try {
    npm config set proxy $ProxyUrl
    npm config set https-proxy $ProxyUrl
    Write-Host "✓ npm configurado" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ Error en npm: $_" -ForegroundColor $ErrorColor
}

# 5. pip
Write-Host "`n[5/6] Actualizando pip..." -ForegroundColor $InfoColor
try {
    python -m pip config set global.proxy $ProxyUrl | Out-Null
    $pipProxyCheck = python -m pip config list | Select-String 'proxy'
    Write-Host "✓ pip configurado: $pipProxyCheck" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ Error en pip: $_" -ForegroundColor $ErrorColor
}

# 6. VS Code
Write-Host "`n[6/6] Actualizando VS Code..." -ForegroundColor $InfoColor
try {
    $settingsPath = Join-Path $env:APPDATA "Code\User\settings.json"
    if (Test-Path $settingsPath) {
        $content = Get-Content -Path $settingsPath -Raw
        # Actualizar http.proxy y añadir http.proxyStrictSSL si no existe
        $content = [Regex]::Replace($content, '"http\.proxy"\s*:\s*"[^"]*"', '"http.proxy": "' + $ProxyUrl + '"')
        if (-not ($content -match '"http\.proxyStrictSSL"')) {
            $content = $content -replace '("http\.proxy":\s*"[^"]*",)', ('$1' + [System.Environment]::NewLine + '  "http.proxyStrictSSL": false,')
        } else {
            $content = [Regex]::Replace($content, '"http\.proxyStrictSSL"\s*:\s*(true|false)', '"http.proxyStrictSSL": false')
        }
        Set-Content -Path $settingsPath -Value $content -Encoding UTF8
        Write-Host "✓ VS Code configurado ($settingsPath)" -ForegroundColor $SuccessColor
    } else {
        Write-Host "⚠ VS Code settings.json no encontrado" -ForegroundColor 'Yellow'
    }
} catch {
    Write-Host "✗ Error en VS Code: $_" -ForegroundColor $ErrorColor
}

# 7. Perfil de PowerShell (set-proxy.ps1)
Write-Host "`n[7/7] Actualizando perfil de PowerShell..." -ForegroundColor $InfoColor
try {
    $setProxyPath = "C:\Users\pablo.salamone\Programmes\Settings\set-proxy.ps1"
    if (Test-Path $setProxyPath) {
        $setProxyContent = @"
# set-proxy.ps1
`$proxy = "$ProxyUrl"

git config --global http.proxy  `$proxy
git config --global https.proxy `$proxy
git config --global http.sslBackend openssl

setx HTTP_PROXY  `$proxy
setx HTTPS_PROXY `$proxy

Write-Host "Proxy corporativo configurado."
"@
        Set-Content -Path $setProxyPath -Value $setProxyContent -Encoding UTF8
        Write-Host "✓ Perfil de PowerShell actualizado ($setProxyPath)" -ForegroundColor $SuccessColor
    } else {
        Write-Host "⚠ Perfil de PowerShell (set-proxy.ps1) no encontrado" -ForegroundColor 'Yellow'
    }
} catch {
    Write-Host "✗ Error en perfil de PowerShell: $_" -ForegroundColor $ErrorColor
}

# Verificación final
Write-Host "`n" + "=" * 60 -ForegroundColor $InfoColor
Write-Host "VERIFICACIÓN FINAL" -ForegroundColor $InfoColor
Write-Host "=" * 60

Write-Host "`nVariables de entorno:" -ForegroundColor $InfoColor
Write-Host "HTTP_PROXY = $env:HTTP_PROXY"

Write-Host "`nGit:" -ForegroundColor $InfoColor
$gitProxy = git config --global --get http.proxy
if ($gitProxy) { Write-Host "http.proxy = $gitProxy" } else { Write-Host "No configurado" }

Write-Host "`npm:" -ForegroundColor $InfoColor
npm config list -l | Select-String 'proxy' | Select-Object -First 2

Write-Host "`nPip:" -ForegroundColor $InfoColor
python -m pip config list | Select-String 'proxy'

Write-Host "`nVS Code:" -ForegroundColor $InfoColor
$settingsPath = Join-Path $env:APPDATA "Code\User\settings.json"
if (Test-Path $settingsPath) {
    Select-String -Path $settingsPath -Pattern '"http\.(proxy|proxyStrictSSL)"' | ForEach-Object { $_.Line }
}

Write-Host "`nPerfil PowerShell:" -ForegroundColor $InfoColor
$setProxyPath = "C:\Users\pablo.salamone\Programmes\Settings\set-proxy.ps1"
if (Test-Path $setProxyPath) {
    Select-String -Path $setProxyPath -Pattern '\$proxy = ' | ForEach-Object { $_.Line }
}

Write-Host "`n" + "=" * 60 -ForegroundColor $SuccessColor
Write-Host "¡ACTUALIZACIÓN COMPLETADA!" -ForegroundColor $SuccessColor
Write-Host "=" * 60

Write-Host "`nNota: Cierra y reabre VS Code y PowerShell para que aplique en nuevas sesiones." -ForegroundColor 'Yellow'
