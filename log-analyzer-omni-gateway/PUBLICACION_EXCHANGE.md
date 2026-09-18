# Guía de Publicación: log-analyzer-omni-gateway en Anypoint Exchange

## 📋 Resumen Ejecutivo
Este documento proporciona instrucciones paso a paso para publicar el **log-analyzer-omni-gateway** en Anypoint Exchange, haciendo que sea reutilizable por otros equipos en tu organización de MuleSoft.

## ✅ Pre-requisitos

Antes de comenzar, asegúrate de tener:

1. **Acceso a Anypoint Platform**: https://anypoint.mulesoft.com
   - Username y password de tu organización
   - Permisos de publicación en Exchange

2. **Instalación local**:
   - Maven 3.8.0 o superior
   - Git (opcional pero recomendado)
   - Java Development Kit (JDK) 11 o 17+

3. **Configuración Maven**:
   - El archivo `~/.m2/settings.xml` con credenciales de Anypoint

4. **Proyecto validado**:
   - `pom.xml` - ✅ Actualizado con distributionManagement
   - `exchange.json` - ✅ Creado con metadatos
   - `log-analyzer-omni-gateway.xml` - Validado
   - Documentación README.md - Recomendado

## 🔐 Paso 1: Obtener Token de Anypoint

### Opción A: Usar Anypoint Platform UI (Recomendado)

1. Accede a https://anypoint.mulesoft.com
2. Navega a **Access Management** → **Users**
3. Selecciona tu usuario
4. Ve a la sección **API tokens**
5. Haz clic en **Create token**
6. Copia el token generado (NO lo compartas)

### Opción B: Usar Curl

```bash
curl -X POST https://anypoint.mulesoft.com/accounts/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your-email@company.com","password":"your-password"}'
```

**Salida esperada**:
```json
{
  "access_token": "your_token_here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 📝 Paso 2: Configurar Maven Settings

Edita el archivo `~/.m2/settings.xml` (crea uno si no existe):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 
          http://maven.apache.org/xsd/settings-1.0.0.xsd">
    
    <servers>
        <!-- Anypoint Exchange Repository -->
        <server>
            <id>anypoint-exchange-v3</id>
            <username>~~~</username>
            <password>${env.ANYPOINT_TOKEN}</password>
        </server>
    </servers>

    <!-- Optional: Proxy Configuration -->
    <!-- Descomenta si usas proxy corporativo
    <proxies>
        <proxy>
            <id>corporate-proxy</id>
            <active>true</active>
            <protocol>http</protocol>
            <host>proxy.company.com</host>
            <port>8080</port>
        </proxy>
    </proxies>
    -->
</settings>
```

## 🔑 Paso 3: Configurar Variables de Entorno

### Windows PowerShell

```powershell
# Obtén tu token de Anypoint
$token = "eyJhbGc..."  # Tu token completo

# Establece la variable de entorno
$env:ANYPOINT_TOKEN = $token

# Verifica que está configurada
echo $env:ANYPOINT_TOKEN
```

### Windows CMD

```cmd
set ANYPOINT_TOKEN=eyJhbGc...
echo %ANYPOINT_TOKEN%
```

### Linux/Mac

```bash
export ANYPOINT_TOKEN="eyJhbGc..."
echo $ANYPOINT_TOKEN
```

## 📦 Paso 4: Preparar el Proyecto

### 4.1 Actualizar información en pom.xml

Abre `log-analyzer-omni-gateway/pom.xml` y valida/actualiza:

```xml
<!-- Estos valores determinan cómo aparecerá en Exchange -->
<groupId>com.mycompany</groupId>                    <!-- Cambiar si es necesario -->
<artifactId>log-analyzer-omni-gateway</artifactId>  <!-- ID único en Exchange -->
<version>1.0.0</version>                             <!-- Incrementar para nuevas versiones -->
<packaging>mule-application</packaging>

<name>log-analyzer-omni-gateway</name>
<description>Descripción clara para Exchange</description>
```

### 4.2 Validar exchange.json

El archivo `log-analyzer-omni-gateway/exchange.json` ya contiene:
- Nombre y descripción
- Tags para búsqueda
- Versión de Mule mínima
- Información de autores

**Personalización recomendada**:

```json
{
  "organizationId": "your-org-id",      // Obtén de Anypoint Platform
  "authors": [
    {
      "name": "Tu Nombre",
      "email": "email@company.com"
    }
  ],
  "visibility": "PUBLIC"  // Cambiar a "PRIVATE" si es necesario
}
```

### 4.3 Crear/Actualizar README.md

Crea un archivo `log-analyzer-omni-gateway/README.md`:

```markdown
# Log Analyzer Omni Gateway

Omni Gateway que expone un Agente de Análisis de Logs con integración a OLLAMA y ServiceNow.

## Features
- Análisis automático de logs con IA
- Integración con ServiceNow para creación de incidentes
- Escalable y configurable

## Installation
1. Descargar desde Exchange
2. Abrir en Anypoint Studio
3. Configurar propiedades globales
4. Deployar a Runtime Fabric o CloudHub

## Configuration
Ver documentación en la carpeta `/docs` o en Anypoint Exchange

## Requirements
- Mule Runtime 4.11.0 o superior
- Java 11+
```

## 🚀 Paso 5: Compilar y Publicar

### 5.1 Compilación local

Navega al directorio del proyecto:

```bash
cd c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA\log-analyzer-omni-gateway
```

Compila el proyecto:

```bash
mvn clean install
```

**Salida esperada**:
```
[INFO] BUILD SUCCESS
[INFO] -------
```

### 5.2 Publicar en Exchange (Opción A: desde PowerShell)

```powershell
# Obtén el token
$token = "eyJhbGc..."

# Establece en ambiente
$env:ANYPOINT_TOKEN = $token

# Publica
mvn deploy
```

### 5.3 Publicar en Exchange (Opción B: usando settings.xml)

```bash
mvn clean package
mvn deploy -Danypoint.token=$ANYPOINT_TOKEN
```

### 5.4 Publicar Versión Final (Sin SNAPSHOT)

Para publicar una versión estable:

```bash
# Actualiza la versión en pom.xml
# Cambia de: 1.0.0-SNAPSHOT
# Cambia a:  1.0.0

mvn versions:set -DnewVersion=1.0.0
mvn clean deploy
```

## 📊 Paso 6: Verificar la Publicación

### 6.1 En Anypoint Platform

1. Accede a https://anypoint.mulesoft.com
2. Navega a **Exchange**
3. Busca: "log-analyzer-omni-gateway"
4. Valida que aparezca con:
   - ✅ Nombre correcto
   - ✅ Descripción visible
   - ✅ Tags aplicados
   - ✅ Versión correcta
   - ✅ Mule version requirement

### 6.2 Verificación via Maven

```bash
# Consulta el repositorio de Exchange
curl -H "Authorization: Bearer $ANYPOINT_TOKEN" \
  "https://maven.anypoint.mulesoft.com/api/v3/maven/com/mycompany/log-analyzer-omni-gateway"
```

## 🔄 Paso 7: Actualizar Versiones Futuras

Para publicar una nueva versión:

```powershell
# 1. Actualiza el código
# 2. Cambia la versión en pom.xml
$env:ANYPOINT_TOKEN = "your_token"

# 3. Compila
mvn clean install

# 4. Publica
mvn deploy

# 5. Verifica en Exchange
```

## 🛠️ Troubleshooting

### Error: "403 Forbidden" o "Unauthorized"

**Causa**: Token de Anypoint inválido o expirado

**Solución**:
1. Genera un nuevo token en Anypoint Platform
2. Actualiza `ANYPOINT_TOKEN` en variables de entorno
3. Verifica que uses `~~~` como username en settings.xml

```powershell
# Limpia credenciales antiguas de Maven
Remove-Item "$env:USERPROFILE\.m2\repository" -Recurse -Force
mvn clean install
```

### Error: "The artifact with coordinate..."

**Causa**: Ya existe una versión publicada con el mismo número

**Solución**:
1. Incrementa el número de versión en `pom.xml`
2. Usa nomenclatura: `1.0.0` → `1.0.1` → `1.1.0` → `2.0.0`
3. Vuelve a compilar y publicar

### Error: "Build Failure - Missing dependencies"

**Causa**: Maven no puede descargar dependencias

**Solución**:
```bash
# Limpia Maven cache
mvn clean
# Reconstruye
mvn -U clean install
```

### Artifact no aparece en Exchange

**Causa**: Revisión pendiente o publicación incorrecta

**Solución**:
1. Espera 5-10 minutos (caché de Exchange)
2. Recarga la página en el navegador (Ctrl+Shift+R)
3. Valida en Deployment Settings que tengas permisos

## 📝 Versionamiento Semántico

Sigue este patrón para versiones:

```
MAJOR.MINOR.PATCH

Ejemplo: 1.2.3
         │ │ │
         │ │ └─ PATCH: Cambios menores, bug fixes (1.2.2 → 1.2.3)
         │ └──── MINOR: Nuevas características, compatible (1.2.0 → 1.3.0)
         └─────── MAJOR: Cambios incompatibles (1.0.0 → 2.0.0)
```

**Reglas**:
- `1.0.0-SNAPSHOT`: Desarrollo
- `1.0.0`: Release estable
- `1.0.1-SNAPSHOT` → `1.0.1`: Patch release
- `1.1.0-SNAPSHOT` → `1.1.0`: Minor release
- `2.0.0-SNAPSHOT` → `2.0.0`: Major release

## 🔒 Consideraciones de Seguridad

1. **Nunca** compartas tu token de Anypoint
2. **Nunca** haz commit de credenciales a Git
3. Usa variables de entorno o `.m2/settings.xml` local
4. Para CI/CD, usa secrets seguros (GitHub Secrets, Jenkins Credentials, etc.)
5. Rota tokens regularmente

## ✨ Paso 8: Socializar en la Organización

Una vez publicado:

1. Notifica al equipo de integración
2. Comparte el enlace de Exchange
3. Documenta en wikis/confluence interno
4. Añade a catálogo de APIs si aplica

## 📞 Soporte

Para problemas:
- **Documentación oficial**: https://docs.mulesoft.com/exchange/
- **Comunidad MuleSoft**: https://www.mulesoft.org/
- **Support Portal**: https://support.mulesoft.com

---

**Última actualización**: 2026-09-02
**Estado**: ✅ Listo para publicar
