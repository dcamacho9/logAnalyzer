# Script PowerShell para Compilar y Desplegar en CloudHub
# Ejecutar desde la carpeta: log-analyzer-omni-gateway

# ============================================================
# CONFIGURACIÓN
# ============================================================
$AppName = "log-analyzer-omni-gateway"
$Environment = "Production"  # O "Staging", "Development"
$Workers = 1
$WorkerType = "SMALL"  # SMALL, MEDIUM, LARGE
$Region = "us-east-1"
$AnyPointUsername = $env:ANYPOINT_USERNAME
$AnyPointPassword = $env:ANYPOINT_PASSWORD

# ============================================================
# COLORES PARA OUTPUT
# ============================================================
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

# ============================================================
# VERIFICAR PRERREQUISITOS
# ============================================================
Write-Info "Verificando prerrequisitos..."

# Verificar Maven
if (-not (Get-Command mvn -ErrorAction SilentlyContinue)) {
    Write-Error "Maven no está instalado o no está en PATH"
    Write-Info "Descárgalo desde: https://maven.apache.org/download.cgi"
    exit 1
}
Write-Success "Maven encontrado: $(mvn --version | Select-Object -First 1)"

# Verificar Java
if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    Write-Error "Java no está instalado o no está en PATH"
    Write-Info "Descárgalo desde: https://www.oracle.com/java/technologies/downloads/"
    exit 1
}
Write-Success "Java encontrado: $(java -version 2>&1 | Select-Object -First 1)"

# Verificar que estamos en la carpeta correcta
if (-not (Test-Path ".\pom.xml")) {
    Write-Error "No se encontró pom.xml en la carpeta actual"
    Write-Info "Ejecuta este script desde la carpeta: log-analyzer-omni-gateway"
    exit 1
}
Write-Success "Ubicación correcta: $(Get-Location)"

# ============================================================
# PASO 1: LIMPIAR BUILD ANTERIOR
# ============================================================
Write-Info ""
Write-Info "=========================================="
Write-Info "PASO 1: Limpiar build anterior"
Write-Info "=========================================="

mvn clean
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error durante 'mvn clean'"
    exit 1
}
Write-Success "Carpeta target limpiada"

# ============================================================
# PASO 2: COMPILAR LA APLICACIÓN
# ============================================================
Write-Info ""
Write-Info "=========================================="
Write-Info "PASO 2: Compilar aplicación para CloudHub"
Write-Info "=========================================="

mvn package
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error durante 'mvn package'"
    Write-Warning "Revisa el log de errores arriba"
    exit 1
}
Write-Success "Compilación exitosa"

# ============================================================
# PASO 3: VERIFICAR JAR
# ============================================================
Write-Info ""
Write-Info "=========================================="
Write-Info "PASO 3: Verificar archivo JAR generado"
Write-Info "=========================================="

$JarFile = Get-ChildItem ".\target\*.jar" -Filter "*mule-application.jar" | Select-Object -First 1
if (-not $JarFile) {
    Write-Error "No se encontró archivo .jar en target/"
    exit 1
}

$JarPath = $JarFile.FullName
$JarSize = [math]::Round($JarFile.Length / 1MB, 2)
Write-Success "JAR encontrado: $($JarFile.Name) ($JarSize MB)"

# ============================================================
# PASO 4: MOSTRAR INFORMACIÓN DE DEPLOYMENT
# ============================================================
Write-Info ""
Write-Info "=========================================="
Write-Info "INFORMACIÓN DE DEPLOYMENT"
Write-Info "=========================================="

Write-Host "Aplicación: $AppName"
Write-Host "Ambiente: $Environment"
Write-Host "Región: $Region"
Write-Host "Workers: $Workers"
Write-Host "Worker Type: $WorkerType"
Write-Host "JAR: $($JarFile.Name)"
Write-Host ""

# ============================================================
# PASO 5: INSTRUCCIONES DE DEPLOYMENT
# ============================================================
Write-Info ""
Write-Info "=========================================="
Write-Info "OPCIONES DE DEPLOYMENT"
Write-Info "=========================================="

Write-Host ""
Write-Host "OPCIÓN 1: Desplegar desde línea de comandos (Maven)"
Write-Host "────────────────────────────────────────────────────"
Write-Host @"
`$env:ANYPOINT_USERNAME = "tu_usuario_anypoint"
`$env:ANYPOINT_PASSWORD = "tu_token_anypoint"

mvn clean package mule:deploy `
  -Dmule.artifact="$JarPath" `
  -Danypoint.username="`$env:ANYPOINT_USERNAME" `
  -Danypoint.password="`$env:ANYPOINT_PASSWORD" `
  -Dapp.name="$AppName" `
  -Dapp.environment="$Environment" `
  -Dapp.workers="$Workers" `
  -Dapp.workertype="$WorkerType" `
  -Dapp.region="$Region"
"@

Write-Host ""
Write-Host "OPCIÓN 2: Desplegar desde Anypoint Studio"
Write-Host "──────────────────────────────────────────"
Write-Host @"
1. Abrir Anypoint Studio
2. Right-click en el proyecto
3. Seleccionar: Anypoint Platform > Deploy to Cloud
4. Rellenar los datos:
   - App Name: $AppName
   - Environment: $Environment
   - Workers: $Workers
   - Worker Type: $WorkerType
   - Region: $Region
5. Click Deploy
"@

Write-Host ""
Write-Host "OPCIÓN 3: Desplegar desde CloudHub Web UI"
Write-Host "──────────────────────────────────────────"
Write-Host @"
1. Ir a: https://anypoint.mulesoft.com > CloudHub
2. Click en 'Deploy application'
3. Subir archivo: $($JarFile.Name)
4. Rellenar datos y hacer click Deploy
"@

# ============================================================
# COPIAR JAR PARA FÁCIL ACCESO
# ============================================================
Write-Info ""
Write-Info "=========================================="
Write-Info "Copiando JAR para fácil acceso"
Write-Info "=========================================="

$DestinationFolder = ".\target\for-cloudhub"
if (-not (Test-Path $DestinationFolder)) {
    New-Item -ItemType Directory -Path $DestinationFolder | Out-Null
}

Copy-Item -Path $JarPath -Destination "$DestinationFolder\$($JarFile.Name)" -Force
Write-Success "JAR copiado a: $DestinationFolder"

# ============================================================
# RESUMEN FINAL
# ============================================================
Write-Info ""
Write-Info "=========================================="
Write-Info "✅ COMPILACIÓN COMPLETADA"
Write-Info "=========================================="
Write-Host ""
Write-Host "Archivo JAR: $JarPath"
Write-Host "Tamaño: $JarSize MB"
Write-Host ""
Write-Host "Próximos pasos:"
Write-Host "1. Configurar credenciales de Anypoint en Maven"
Write-Host "2. Ejecutar uno de los comandos de deployment arriba"
Write-Host "3. O subir el JAR manualmente a CloudHub"
Write-Host ""
Write-Info "Para más información, ver: CLOUDHUB_DEPLOYMENT_GUIDE.md"
Write-Host ""
