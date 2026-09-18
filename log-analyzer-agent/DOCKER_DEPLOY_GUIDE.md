# Docker Build y Deploy en Render - Guía Completa

## Resumen

Este archivo te guía para:
1. ✅ Construir imagen Docker de `log-analyzer-agent`
2. ✅ Subirla a Docker Hub
3. ✅ Desplegar en Render usando la imagen

## Prerequisitos

### Local
- Docker Desktop instalado: https://www.docker.com/products/docker-desktop
- Docker running
- Git instalado

### Docker Hub
- Cuenta en Docker Hub: https://hub.docker.com
- GitHub token (opcional, para privadas)

### Render
- Cuenta en Render: https://render.com (gratis)

---

## Paso 1: Preparar tu Repositorio

### 1.1 Asegúrate que todo está en Git

```powershell
cd c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA

# Ver estado actual
git status

# Añadir cambios
git add .

# Commit
git commit -m "Docker setup para log-analyzer-agent"

# Push
git push origin main
```

### 1.2 Verificar archivos críticos

```powershell
# Debe existir
ls log-analyzer-agent/Dockerfile
ls log-analyzer-agent/.dockerignore
ls log-analyzer-agent/requeriments.txt
ls log-analyzer-agent/api.py
```

---

## Paso 2: Build Imagen Docker Localmente

### Opción A: Con Script PowerShell (RECOMENDADO)

```powershell
# Navega a la raíz del proyecto
cd c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA

# Ejecuta el script (ver docker-build-push.ps1)
.\docker-build-push.ps1
```

### Opción B: Manual

```powershell
cd c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA\log-analyzer-agent

# Build con tag
docker build -t log-analyzer-agent:latest -t log-analyzer-agent:v1.0.0 .

# Verificar que se construyó
docker images | grep log-analyzer-agent

# Probar localmente (opcional)
docker run -p 5000:5000 \
  -e OLLAMA_API_URL=http://host.docker.internal:11434 \
  -e MODEL_NAME=log-analyzer-agent \
  log-analyzer-agent:latest
```

---

## Paso 3: Push a Docker Hub

### 3.1 Crear Token en Docker Hub

1. Ve a: https://hub.docker.com/settings/security
2. Click en "New Access Token"
3. Nombre: `docker-push-token`
4. Permisos: `Read & Write`
5. Copia el token

### 3.2 Login en Docker

```powershell
# Tu username de Docker Hub
$username = "tu_username_docker"

# Solicita contraseña
docker login -u $username

# Pega el token cuando pida password
```

### 3.3 Tag y Push

```powershell
# Tag con tu usuario
docker tag log-analyzer-agent:latest $username/log-analyzer-agent:latest
docker tag log-analyzer-agent:v1.0.0 $username/log-analyzer-agent:v1.0.0

# Push
docker push $username/log-analyzer-agent:latest
docker push $username/log-analyzer-agent:v1.0.0

# Verificar en https://hub.docker.com/r/tu_username/log-analyzer-agent
```

---

## Paso 4: Desplegar en Render

### 4.1 Crear Web Service en Render

1. Ve a: https://dashboard.render.com
2. Click en "New +" → "Web Service"
3. Selecciona "Public Git Repository"
4. Conecta tu repo de GitHub

### 4.2 Configurar Deployment

**Sección General:**
- Name: `log-analyzer-agent`
- Region: Frankfurt (EU) o US (East)
- Branch: `main`

**Sección Build:**
- Build Command: (dejar vacío)
- Start Command: (dejar vacío)

**Sección Docker:**
- Activar: "Use Docker Image"
- Image URL: `docker.io/tu_username/log-analyzer-agent:latest`
- OR private: Proporcionar Docker credentials si es privada

**Sección Environment:**
Añade variables (ver .env.example):

```
OLLAMA_API_URL=https://tu-ollama-cloudflare-tunnel.com:11434
MODEL_NAME=log-analyzer-agent
SERVICENOW_INSTANCE=tu-instancia
SERVICENOW_CLIENT_ID=xxx
SERVICENOW_CLIENT_SECRET=xxx
```

### 4.3 Deploy

Click en "Create Web Service"

Render:
- Descargará la imagen de Docker Hub
- La ejecutará en su infraestructura
- Te dará una URL: `https://log-analyzer-agent.onrender.com`

---

## Paso 5: Verificar Deployment

### Test Health Endpoint

```powershell
# Obtén tu URL de Render
$url = "https://log-analyzer-agent.onrender.com"

# Test
curl.exe "$url/api/health"

# Debe retornar: { "status": "ok" }
```

### Test Endpoint de Analyze

```powershell
$json = @{
    limit = 10
} | ConvertTo-Json

curl.exe -X POST "$url/api/analyze" `
  -H "Content-Type: application/json" `
  -d $json
```

---

## Troubleshooting

### Error 503: Service Unavailable
- Render está iniciando (espera 2 min)
- Plan Free pausó el servicio → cambiar a Starter Plan

### Error 502: Bad Gateway
- OLLAMA_API_URL incorrea o no accesible
- Verificar Cloudflare Tunnel está activo
- Verificar variables de entorno en Render

### Error 404 en /api/health
- API no está escuchando en puerto correcto
- Verificar que PORT=5000 en Dockerfile

### Container crashea
Ver logs en Render:
1. Dashboard → log-analyzer-agent
2. Click en "Logs"
3. Busca errores

---

## Script Automatizado (docker-build-push.ps1)

Crea este archivo en la raíz del proyecto:

```powershell
# IMPORTANTE: Personaliza estas variables
$DOCKER_USERNAME = "tu_username"
$IMAGE_NAME = "log-analyzer-agent"
$TAG_VERSION = "v1.0.0"

# Build
Write-Host "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${TAG_VERSION} `
  -f log-analyzer-agent/Dockerfile `
  log-analyzer-agent

# Tag para Docker Hub
Write-Host "🏷️  Tagging for Docker Hub..."
docker tag ${IMAGE_NAME}:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
docker tag ${IMAGE_NAME}:${TAG_VERSION} ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG_VERSION}

# Push
Write-Host "📤 Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG_VERSION}

# Status
Write-Host "✅ Done! Image available at:"
Write-Host "   docker.io/${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
Write-Host "   docker.io/${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG_VERSION}"
```

---

## Alternativa: Render Native Deployment (sin Docker Hub)

Si prefieres que Render construya la imagen:

1. Asegúrate que Dockerfile esté en raíz del repo
2. En Render, selecciona "Dockerfile" en lugar de "Public Git Repository"
3. Render construirá automáticamente en cada push

**Ventaja:** No necesitas Docker Hub
**Desventaja:** Build toma ~5-10 min en lugar de segundos

---

## Actualizar Imagen en Render

### Opción 1: Auto Deploy en Git Push
- Render automáticamente redeploy cuando hacer push a main

### Opción 2: Manual desde Docker Hub
```powershell
# Actualizar código
git commit -am "bugfix"
git push

# Rebuild y push imagen
docker build -t mi_usuario/log-analyzer-agent:latest log-analyzer-agent
docker push mi_usuario/log-analyzer-agent:latest

# Render se actualizará automáticamente (espera 1-5 min)
```

---

## Estadísticas de Costo

| Recurso | Costo Mensual |
|---------|---|
| Render Starter Plan | $7 USD |
| Docker Hub Public | $0 USD |
| OLLAMA local (Cloudflare) | $0 USD |
| **TOTAL** | **~$7 USD** |

---

## Referencias

- Docker Docs: https://docs.docker.com
- Docker Hub: https://hub.docker.com
- Render Docs: https://docs.render.com
- Dockerfile Best Practices: https://docs.docker.com/develop/dev-best-practices/dockerfile_best-practices/
