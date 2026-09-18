# Automatización CI/CD para Publicación en Exchange

Guía para configurar pipelines automáticos de publicación en Anypoint Exchange.

## GitHub Actions (Recomendado)

Crea el archivo `.github/workflows/publish-to-exchange.yml`:

```yaml
name: Publish to Anypoint Exchange

on:
  push:
    tags:
      - 'v*.*.*'  # Publica solo con tags de versión (v1.0.0, v1.0.1, etc)

jobs:
  publish:
    runs-on: windows-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up JDK 11
        uses: actions/setup-java@v3
        with:
          java-version: '11'
          distribution: 'adopt'
          cache: maven
      
      - name: Extract version from tag
        id: version
        run: |
          $tag = ${{ github.ref }}
          $version = $tag -replace 'refs/tags/v', ''
          echo "VERSION=$version" >> $env:GITHUB_OUTPUT
      
      - name: Update pom.xml version
        run: |
          mvn versions:set -DnewVersion=${{ steps.version.outputs.VERSION }} -f log-analyzer-omni-gateway/pom.xml
      
      - name: Build with Maven
        run: |
          mvn clean install -f log-analyzer-omni-gateway/pom.xml
      
      - name: Publish to Exchange
        run: |
          mvn deploy -f log-analyzer-omni-gateway/pom.xml
        env:
          ANYPOINT_TOKEN: ${{ secrets.ANYPOINT_TOKEN }}
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ steps.version.outputs.VERSION }}
          body: |
            Published to Anypoint Exchange
            Version: ${{ steps.version.outputs.VERSION }}
            
            Asset: log-analyzer-omni-gateway
            URL: https://anypoint.mulesoft.com/exchange/api/v1/assets/com.mycompany/log-analyzer-omni-gateway/${{ steps.version.outputs.VERSION }}
          draft: false
          prerelease: false
```

### Configuración Inicial

1. **Obtén el token de Anypoint** (ver PUBLICACION_EXCHANGE.md)

2. **Añade el secret a GitHub**:
   - Ve a tu repo en GitHub
   - **Settings** → **Secrets and variables** → **Actions**
   - **New repository secret**
   - Name: `ANYPOINT_TOKEN`
   - Value: Tu token completo (sin comillas)

3. **Usa el pipeline**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

---

## GitLab CI/CD

Crea `.gitlab-ci.yml`:

```yaml
stages:
  - build
  - deploy

variables:
  MAVEN_CLI_OPTS: "-s .m2/settings.xml -DskipTests"

before_script:
  - cd log-analyzer-omni-gateway

build:
  stage: build
  image: maven:3.8.1-jdk-11
  script:
    - mvn clean install
  only:
    - tags
  artifacts:
    paths:
      - target/

publish_exchange:
  stage: deploy
  image: maven:3.8.1-jdk-11
  script:
    - mvn versions:set -DnewVersion=$CI_COMMIT_TAG
    - mvn clean install
    - mvn deploy
  only:
    - tags
  environment:
    name: exchange
    url: https://anypoint.mulesoft.com/exchange/
```

### Configuración de Variables

En GitLab (**Settings** → **CI/CD** → **Variables**):

```
ANYPOINT_TOKEN = tu_token_aqui
```

---

## Jenkins Pipeline

Crea `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    parameters {
        string(name: 'VERSION', defaultValue: '1.0.0', description: 'Version to publish')
    }
    
    environment {
        PROJECT_DIR = 'log-analyzer-omni-gateway'
        ANYPOINT_TOKEN = credentials('anypoint-token')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                dir("${PROJECT_DIR}") {
                    sh 'mvn clean install'
                }
            }
        }
        
        stage('Update Version') {
            steps {
                dir("${PROJECT_DIR}") {
                    sh "mvn versions:set -DnewVersion=${params.VERSION}"
                }
            }
        }
        
        stage('Publish to Exchange') {
            steps {
                dir("${PROJECT_DIR}") {
                    withEnv(["ANYPOINT_TOKEN=${ANYPOINT_TOKEN}"]) {
                        sh 'mvn deploy'
                    }
                }
            }
        }
        
        stage('Verify Publication') {
            steps {
                script {
                    echo "✓ Publicado en Exchange v${params.VERSION}"
                    echo "URL: https://anypoint.mulesoft.com/exchange/api/v1/assets/com.mycompany/log-analyzer-omni-gateway/${params.VERSION}"
                }
            }
        }
    }
    
    post {
        success {
            echo "✓ Pipeline exitoso - Publicación completada"
        }
        failure {
            echo "✗ Pipeline falló - Revisa los logs"
        }
    }
}
```

### Configuración Jenkins

1. **Manage Jenkins** → **Credentials** → **Global**
2. **Add Credentials** → **Secret text**
   - Secret: Tu token de Anypoint
   - ID: `anypoint-token`

3. **Nueva Job** → **Pipeline**
4. **Pipeline script** → **SCM** → **Git**
5. **Repository URL**: Tu repo
6. **Script path**: `Jenkinsfile`

---

## Azure DevOps Pipeline

Crea `azure-pipelines.yml`:

```yaml
trigger:
  tags:
    include:
      - 'v*'

pool:
  vmImage: 'windows-latest'

variables:
  projectDir: 'log-analyzer-omni-gateway'
  mavenVersion: '3.8.1'

stages:
  - stage: Build
    jobs:
      - job: BuildArtifact
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.8'
          
          - task: Maven@3
            inputs:
              mavenPomFile: '$(projectDir)/pom.xml'
              mavenOptions: '-Xmx3072m'
              javaHomeOption: 'JDKVersion'
              jdkVersionOption: '1.11'
              jdkArchitectureOption: 'x64'
              publishJUnitResults: true
              testResultsFiles: '**/surefire-reports/TEST-*.xml'
              goals: 'clean install'

  - stage: Publish
    jobs:
      - job: PublishToExchange
        steps:
          - task: Maven@3
            inputs:
              mavenPomFile: '$(projectDir)/pom.xml'
              javaHomeOption: 'JDKVersion'
              jdkVersionOption: '1.11'
              goals: 'deploy'
            env:
              ANYPOINT_TOKEN: $(anypointToken)
          
          - script: |
              echo "##[group]Publication Summary"
              echo "Artifact: log-analyzer-omni-gateway"
              echo "Version: $(Build.SourceBranchName)"
              echo "Repository: Anypoint Exchange"
              echo "##[endgroup]"
```

### Configuración en Azure DevOps

1. **Pipeline** → **Edit**
2. **Variables** → **New**
   - Name: `anypointToken`
   - Value: Tu token (marcar como secret)
   - Scope: Pipeline

---

## Decisión de Plataforma

| Plataforma | Ventajas | Ideal Para |
|-----------|----------|-----------|
| **GitHub Actions** | Gratuito, fácil, integrado | Proyectos open-source, GitHub.com |
| **GitLab CI** | Robusto, gratuito, entorno completo | Equipos GitLab/on-premise |
| **Jenkins** | Máxima flexibilidad, autodesplegado | Empresas con Jenkins existente |
| **Azure DevOps** | Integración con ecosistema Azure | Organizaciones Microsoft |

---

## Mejores Prácticas

### 1. Gestión de Versiones

```bash
# Desarrollo
git checkout -b feature/new-feature
mvn versions:set -DnewVersion=1.1.0-SNAPSHOT

# Release
git tag v1.1.0
mvn versions:set -DnewVersion=1.1.0
git push origin v1.1.0  # Dispara pipeline automático
```

### 2. Seguridad

- ✅ Usar secrets seguros para el token
- ✅ Nunca hacer commit del token
- ✅ Rotar tokens regularmente
- ✅ Auditar acceso a secrets
- ✅ Usar permisos mínimos (menor privilege)

### 3. Notificaciones

```yaml
# Ejemplo para GitHub Actions
- name: Notify on Success
  if: success()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'log-analyzer-omni-gateway v${{ steps.version.outputs.VERSION }} publicado en Exchange'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}

- name: Notify on Failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Publicación fallida - Revisa los logs'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 4. Validaciones

```yaml
# Validar que pom.xml está actualizado
- name: Validate pom.xml
  run: |
    VERSION=$(grep '<version>' pom.xml | head -1 | sed 's/.*<version>\(.*\)<\/version>.*/\1/')
    if [[ $VERSION == *"SNAPSHOT"* ]]; then
      echo "❌ No se puede publicar versión SNAPSHOT"
      exit 1
    fi
    echo "✓ Versión válida para publicar: $VERSION"
```

### 5. Rollback

```bash
# Si la publicación fue correcta pero necesitas un rollback:

# 1. Retira la versión de Exchange (manual desde UI)
# 2. O incrementa la versión y vuelve a publicar:
git tag v1.1.1  # Nueva versión patch
git push origin v1.1.1
```

---

## Monitoreo y Alertas

### Verificar publicaciones

```powershell
# Script PowerShell para verificar publicaciones recientes
$token = $env:ANYPOINT_TOKEN
$headers = @{"Authorization" = "Bearer $token"}

$response = Invoke-WebRequest `
  -Uri "https://maven.anypoint.mulesoft.com/api/v3/maven/com/mycompany/log-analyzer-omni-gateway" `
  -Headers $headers

$response.Content | ConvertFrom-Json | Select-Object -ExpandProperty version | Sort-Object -Descending | Select-Object -First 5
```

---

## Troubleshooting CI/CD

| Problema | Causa | Solución |
|----------|-------|----------|
| **Token expirado** | Token de Anypoint vencido | Genera uno nuevo y actualiza secret |
| **Build timeout** | Maven lento descargando deps | Aumenta timeout en pipeline |
| **Permission denied** | Secret mal configurado | Verifica nombre de secret coincida |
| **No trigger** | Tag pattern incorrecto | Verifica pattern en configuración |

---

**Última actualización**: 2026-09-02
**Estado**: ✅ Listo para implementar
