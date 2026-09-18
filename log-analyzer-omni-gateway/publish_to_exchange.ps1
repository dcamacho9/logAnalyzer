# Script de Publicación en Anypoint Exchange
# Automatiza el proceso de compilación y publicación del log-analyzer-omni-gateway
# 
# Uso: .\publish_to_exchange.ps1 -Token "eyJhbGc..." -Version "1.0.0"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = ".",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

# Configuración
$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  log-analyzer-omni-gateway - Publicación en Exchange       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Funciones auxiliares
function Log-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Log-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Log-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "┌─────────────────────────────────────────────────────────┐" -ForegroundColor Blue
    Write-Host "│ $Message" -ForegroundColor Blue
    Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor Blue
}

# Validaciones iniciales
Log-Step "Validando Pre-requisitos"

# Verifica Maven
try {
    $mvnVersion = mvn -v 2>$null | Select-Object -First 1
    Log-Info "Maven encontrado: $mvnVersion"
} catch {
    Log-Error "Maven no está instalado o no está en el PATH"
    exit 1
}

# Verifica que el proyecto existe
if (-not (Test-Path "$ProjectPath\pom.xml")) {
    Log-Error "No se encontró pom.xml en: $ProjectPath"
    exit 1
}
Log-Info "Proyecto encontrado: $ProjectPath"

# Valida el token
if ([string]::IsNullOrEmpty($Token)) {
    Log-Error "Token de Anypoint es requerido"
    exit 1
}
Log-Info "Token de Anypoint validado (longitud: $($Token.Length) caracteres)"

# Establece variable de entorno
$env:ANYPOINT_TOKEN = $Token
Log-Info "Variable ANYPOINT_TOKEN configurada"

# Lee el pom.xml actual
Log-Step "Validando Configuración del Proyecto"

[xml]$pomXml = Get-Content "$ProjectPath\pom.xml"
$currentGroupId = $pomXml.project.groupId
$currentArtifactId = $pomXml.project.artifactId
$currentVersion = $pomXml.project.version

Log-Info "GroupId: $currentGroupId"
Log-Info "ArtifactId: $currentArtifactId"
Log-Info "Versión actual (pom.xml): $currentVersion"
Log-Info "Versión a publicar: $Version"

# Compila el proyecto
Log-Step "Compilando Proyecto"

Push-Location $ProjectPath

if ($SkipTests) {
    Log-Info "Saltando pruebas (--skip-tests)"
    $buildResult = mvn clean install -DskipTests
} else {
    Log-Info "Ejecutando pruebas"
    $buildResult = mvn clean install
}

if ($LASTEXITCODE -ne 0) {
    Log-Error "La compilación falló. Revisa los logs arriba."
    Pop-Location
    exit 1
}

Log-Info "✓ Compilación completada exitosamente"

# Actualiza la versión en pom.xml
Log-Step "Actualizando Versión en pom.xml"

Log-Info "Cambio de versión: $currentVersion → $Version"

$updateVersionResult = mvn versions:set -DnewVersion=$Version

if ($LASTEXITCODE -ne 0) {
    Log-Warning "No se pudo actualizar la versión automáticamente"
    Log-Info "Actualiza manualmente en pom.xml y vuelve a intentar"
}

Log-Info "✓ Versión actualizada a: $Version"

# Recompila con la nueva versión
Log-Step "Recompilando con Nueva Versión"

if ($SkipTests) {
    mvn clean install -DskipTests
} else {
    mvn clean install
}

if ($LASTEXITCODE -ne 0) {
    Log-Error "Recompilación con nueva versión falló"
    Pop-Location
    exit 1
}

Log-Info "✓ Recompilación completada"

# Vista previa de publicación
Log-Step "Resumen de Publicación"

Write-Host ""
Write-Host "  GroupId:       $currentGroupId" -ForegroundColor Gray
Write-Host "  ArtifactId:    $currentArtifactId" -ForegroundColor Gray
Write-Host "  Versión:       $Version" -ForegroundColor Yellow
Write-Host "  Destino:       https://maven.anypoint.mulesoft.com/api/v3/maven" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Log-Warning "Modo DRY-RUN: No se realizará la publicación"
    Log-Info "Para publicar realmente, ejecuta sin -DryRun"
    Pop-Location
    exit 0
}

# Confirmación
Write-Host ""
$confirmation = Read-Host "¿Deseas continuar con la publicación? (s/n)"

if ($confirmation -ne "s") {
    Log-Warning "Publicación cancelada por el usuario"
    Pop-Location
    exit 0
}

# Publica en Exchange
Log-Step "Publicando en Anypoint Exchange"

Log-Info "Ejecutando: mvn deploy"
mvn deploy

if ($LASTEXITCODE -ne 0) {
    Log-Error "La publicación en Exchange falló"
    Pop-Location
    exit 1
}

Log-Info "✓ Publicación completada exitosamente"

# Información post-publicación
Log-Step "Verificación Post-Publicación"

$exchangeUrl = "https://anypoint.mulesoft.com/exchange/api/v1/assets/$currentGroupId/$currentArtifactId/$Version"

Log-Info "Artifact publicado en:"
Write-Host "  $exchangeUrl" -ForegroundColor Cyan
Write-Host ""
Log-Info "Verifica en Anypoint Exchange:"
Write-Host "  https://anypoint.mulesoft.com/exchange/" -ForegroundColor Cyan
Write-Host ""

# Próximos pasos
Log-Step "Próximos Pasos"

Write-Host "  1. Espera 5-10 minutos para que Exchange indexe el artifact" -ForegroundColor Gray
Write-Host "  2. Recarga la página de Exchange en tu navegador" -ForegroundColor Gray
Write-Host "  3. Busca: '$currentArtifactId'" -ForegroundColor Gray
Write-Host "  4. Valida que todos los metadatos sean correctos" -ForegroundColor Gray
Write-Host ""

Pop-Location

Log-Info "¡Proceso completado exitosamente!"
Write-Host ""
