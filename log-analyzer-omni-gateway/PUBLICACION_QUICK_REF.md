# Publicar en Exchange - Referencia Rápida

## ⚡ Comandos Rápidos (Copia y Pega)

### PowerShell

```powershell
# 1. Establece tu token
$token = "eyJhbGc..."  # Reemplaza con tu token de Anypoint

# 2. Navega al proyecto
cd "c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA\log-analyzer-omni-gateway"

# 3. Configura variable de entorno
$env:ANYPOINT_TOKEN = $token

# 4. Compila y prueba
mvn clean install

# 5. Publica
mvn deploy

# O usa el script automatizado:
.\publish_to_exchange.ps1 -Token $token -Version "1.0.0"
```

### CMD

```cmd
REM 1. Establece tu token
set ANYPOINT_TOKEN=eyJhbGc...

REM 2. Navega al proyecto
cd c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA\log-analyzer-omni-gateway

REM 3. Compila
mvn clean install

REM 4. Publica
mvn deploy
```

## 🔐 Obtener Token Anypoint

### Opción A: Desde Anypoint Platform

1. Ve a https://anypoint.mulesoft.com
2. **Access Management** → **Users**
3. Selecciona tu usuario
4. **API tokens** → **Create token**
5. Copia el token completo

### Opción B: Curl

```powershell
$response = curl.exe -X POST https://anypoint.mulesoft.com/accounts/login `
  -H "Content-Type: application/json" `
  -d '{"username":"your-email@company.com","password":"your-password"}'

$json = $response | ConvertFrom-Json
$token = $json.access_token
echo $token
```

## 📝 Validación Pre-Publicación

Checklist:

- [ ] pom.xml actualizado con versión correcta
- [ ] exchange.json con metadatos completos
- [ ] README.md con instrucciones de uso
- [ ] Proyecto compila sin errores: `mvn clean install`
- [ ] Tests pasan: `mvn test`
- [ ] Variable ANYPOINT_TOKEN configurada
- [ ] Maven settings.xml con credenciales

## 🚀 Flujo Completo (5 minutos)

```bash
# 1. Prepara el proyecto
cd log-analyzer-omni-gateway
mvn clean install  # ~2 min

# 2. Publica
$env:ANYPOINT_TOKEN = "tu_token"
mvn deploy         # ~1 min

# 3. Verifica (5-10 min después)
# Ve a https://anypoint.mulesoft.com/exchange
# Busca: "log-analyzer-omni-gateway"
```

## 🔍 Verificación Post-Publicación

```powershell
# Opción 1: Visita directamente
Start-Process "https://anypoint.mulesoft.com/exchange/api/v1/assets/com.mycompany/log-analyzer-omni-gateway/1.0.0"

# Opción 2: Busca manualmente
# https://anypoint.mulesoft.com/exchange/
# → Busca "log-analyzer-omni-gateway"

# Opción 3: Curl (requiere token)
curl -H "Authorization: Bearer $env:ANYPOINT_TOKEN" `
  "https://maven.anypoint.mulesoft.com/api/v3/maven/com/mycompany/log-analyzer-omni-gateway"
```

## ❌ Troubleshooting Rápido

| Error | Solución |
|-------|----------|
| **403 Forbidden** | Token inválido/expirado. Genera uno nuevo en Anypoint |
| **Artifact already exists** | Incrementa versión en pom.xml (1.0.0 → 1.0.1) |
| **Maven not found** | Instala Maven o añádelo al PATH |
| **Build failed** | Ejecuta `mvn clean install` para debug |
| **Not visible en Exchange** | Espera 5-10 min, recarga página (Ctrl+Shift+R) |

## 📋 Versionamiento

```
SNAPSHOT     → Desarrollo    (1.0.0-SNAPSHOT)
Release      → Estable       (1.0.0)
Patch        → Bug fix       (1.0.1)
Minor        → Nuevo feature (1.1.0)
Major        → Breaking      (2.0.0)
```

## 🎯 Archivos Clave

```
log-analyzer-omni-gateway/
├── pom.xml                  ← Actualizar versión aquí
├── exchange.json            ← Metadatos (Ya configurado ✓)
├── README.md                ← Instrucciones de uso
├── publish_to_exchange.ps1  ← Script automatizado
├── PUBLICACION_EXCHANGE.md  ← Guía detallada
├── log-analyzer-omni-gateway.xml
└── mule-artifact.json
```

## 📞 Enlaces Útiles

- **Exchange**: https://anypoint.mulesoft.com/exchange/
- **Docs**: https://docs.mulesoft.com/exchange/
- **Anypoint Platform**: https://anypoint.mulesoft.com
- **Maven**: https://maven.apache.org/

---

**Última actualización**: 2026-09-02
