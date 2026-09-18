# PLAN DE CORRECCIÓN - Errores en API Gateway Mapfre

## Resumen Ejecutivo
- **Total de errores identificados**: 12
- **Nivel de urgencia**: 🔴 CRÍTICO (6 errores) + 🟠 ALTO (4) + 🟡 MEDIO (2)
- **Tasa de error**: 3.43% del total de transacciones
- **Tiempo de resolución estimado**: 6-10 horas de trabajo

---

## 🔴 CRÍTICO: Azure Token Validation (6 occurrencias)

### Descripción
El servicio TestAzAudimapADFS rechaza 6 solicitudes consecutivas con tokens válidos. El error ocurre en la capa de autorización después de que el backend devuelve HTTP 200.

### Síntomas
```
[2026-06-08T16:03:10] WARNING: Error in MAP IFW Azure Token Validation-v2.0
Error message: "This token cannot be used with this service"
Response: HTTP 401
```

### Causa Raíz Probable
1. **Token con scopes insuficientes**: El token de Azure AD no incluye el scope para TestAzAudimapADFS
2. **Política de autorización no actualizada**: La política MAP IFW Azure Token Validation-v2.0 requiere claims específicos
3. **Expiración de token**: Tokens con `exp` claim anterior a la hora de la solicitud

### Plan de Corrección

#### Paso 1: Investigación (30 min)
```bash
# En el API Gateway L7tech:
1. Abrir policy editor → "MAP IFW Azure Token Validation-v2.0"
2. Revisar los siguientes assertion policies:
   - Extract Claims from JWT
   - Check Predefined Claims (exp, iat, nbf)
   - Extract Custom Claims (scope, aud)
3. Comparar scopes esperados vs. scopes recibidos
```

#### Paso 2: Validar Azure AD Configuration (30 min)
```bash
# En Azure Portal:
1. Ir a App Registrations → Buscar la app registrada para MAP IFW
2. Verificar "API Permissions":
   - ✅ TestAzAudimapADFS debe estar en permisos delegados
   - ✅ Consentimiento de admin debe estar dado
3. Revisar "Token configuration":
   - ✅ Optional claims para scope debe incluir "scp"
4. Verificar credenciales:
   - ✅ Certificate/Secret no expirado
```

#### Paso 3: Actualizar Policy (1 hora)
```xml
<!-- En MAP IFW Azure Token Validation-v2.0 -->
<!-- Agregar validación de scopes: -->
<l7:Assertion>
  <CheckProtectedVariable>
    <VariableName>claims.scp</VariableName>
    <Patterns>
      <Pattern>.*TestAzAudimapADFS.*</Pattern>
      <Pattern>.*api://TestAzAudimapADFS.*</Pattern>
    </Patterns>
  </CheckProtectedVariable>
</l7:Assertion>

<!-- Agregar validación de expiración explícita: -->
<l7:Assertion>
  <ValidateJsonWebSignature>
    <CheckExpiration>true</CheckExpiration>
    <ClockSkew>300</ClockSkew> <!-- 5 minutos de tolerance -->
  </ValidateJsonWebSignature>
</l7:Assertion>
```

#### Paso 4: Testing (30 min)
```bash
# Request de prueba:
curl -X GET "https://api.mapfre.local/test/srv/audimap/types_structure_report" \
  -H "Authorization: Bearer <VALID_AZURE_TOKEN_WITH_TESTAZAUDIMAPADSFS_SCOPE>" \
  -H "Content-Type: application/json"

# Esperado: HTTP 200 + respuesta válida
# NO: HTTP 401 + MAP IFW Error Template-v2.0
```

#### Paso 5: Deployment (15 min)
```bash
1. Publicar política en DEV
2. Ejecutar request de prueba 10 veces
3. Verificar 0 errores de autorización
4. Promover a QA
5. Promover a PROD (fuera de horas pico)
```

### Métricas de Éxito
- ✅ 0 errores de Azure Token Validation en siguiente hora
- ✅ Tiempo de respuesta: < 100ms (actual: 47ms, aceptable)
- ✅ Tasa de éxito: 100% para TestAzAudimapADFS

### Rollback Plan
```bash
# Si después del cambio aumentan los errores:
1. Revertir la política anterior
2. Verificar logs con: search policy="MAP IFW Azure Token Validation-v2.0"
3. Escalar a Security Team
```

---

## 🟠 ALTO: Duplicate Primary Key - Database (4 occurrencias)

### Descripción
En el endpoint de login, el token se genera exitosamente (HTTP 200) pero falla al persistir en la base de datos por entrada duplicada.

### Síntomas
```
[2026-06-08T16:21:13.666] WARNING: JdbcQueryingManagerImpl
Duplicate entry 'APP-CMPCRTVRDNSE-c679a92b-6a9a-4185-8077-3d065082d811' 
for key 'json_web_token.PRIMARY'
Affected user: APP-CMPCRTVRDNSE
```

### Causa Raíz Probable
1. **Token UUID collision**: Mismo token generado múltiples veces en corto lapso
2. **Falta de cleanup**: Tokens expirados no se eliminan de la BD
3. **Transacción no completada**: Rollback parcial dejó registro anterior

### Plan de Corrección

#### Paso 1: Inspeccionar Base de Datos (30 min)
```sql
-- En MySQL/MariaDB:
USE mapfre_gateway;

-- Ver registros duplicados:
SELECT token_id, user_id, created_at, expires_at, COUNT(*) as duplicates
FROM json_web_token
WHERE token_id LIKE 'APP-CMPCRTVRDNSE%'
GROUP BY token_id, user_id
HAVING COUNT(*) > 1;

-- Ver todas las entradas para este usuario:
SELECT token_id, user_id, created_at, expires_at, is_valid
FROM json_web_token
WHERE user_id = 'APP-CMPCRTVRDNSE'
ORDER BY created_at DESC
LIMIT 20;

-- Verificar expiración:
SELECT COUNT(*) as expired_tokens
FROM json_web_token
WHERE expires_at < NOW();
```

#### Paso 2: Limpiar Base de Datos (45 min)
```sql
-- 1. Eliminar tokens expirados:
DELETE FROM json_web_token
WHERE expires_at < DATE_SUB(NOW(), INTERVAL 24 HOUR)
  AND is_valid = FALSE;

-- 2. Consolidar duplicados (mantener el más reciente):
WITH cte_to_delete AS (
  SELECT token_id, ROW_NUMBER() OVER (PARTITION BY user_id, created_date ORDER BY created_at DESC) as rn
  FROM json_web_token
  WHERE token_id LIKE 'APP-CMPCRTVRDNSE%'
)
DELETE FROM json_web_token
WHERE token_id IN (SELECT token_id FROM cte_to_delete WHERE rn > 1);

-- 3. Crear índice UNIQUE con condición:
ALTER TABLE json_web_token
ADD UNIQUE INDEX idx_unique_active_token (user_id, created_date)
WHERE is_valid = TRUE;

-- 4. Verificar integridad:
CHECK TABLE json_web_token;
```

#### Paso 3: Actualizar Mule Flow (1 hora)
```xml
<!-- En esp/ext/api/frontales/1.0/login flow -->
<!-- Agregar validación antes de INSERT: -->
<mule:flow name="login-flow">
  <!-- ... autenticación ... -->
  
  <!-- Verificar si token ya existe para este usuario en últimos 30 segundos -->
  <mule:until-successful maxRetries="3" millisBetweenRetries="500">
    <db:execute-script>
      <db:sql>
        SELECT COUNT(*) as token_count 
        FROM json_web_token 
        WHERE user_id = :userId 
        AND created_at > DATE_SUB(NOW(), INTERVAL 30 SECOND)
        AND is_valid = TRUE
      </db:sql>
    </db:execute-script>
  </mule:until-successful>
  
  <!-- Si token_count > 0, devolver token existente en lugar de crear nuevo -->
  <mule:choice>
    <mule:when expression="payload.token_count > 0">
      <!-- Devolver token existente -->
      <db:query>
        <db:sql>SELECT * FROM json_web_token WHERE user_id = :userId LIMIT 1</db:sql>
      </db:query>
    </mule:when>
    <mule:otherwise>
      <!-- Crear nuevo token -->
      <db:insert>
        <db:entity-type>json_web_token</db:entity-type>
        <db:values>
          <db:value key="token_id">#[java.util.UUID.randomUUID().toString()]</db:value>
          <db:value key="user_id">#[payload.userId]</db:value>
          <db:value key="token_hash">#[payload.tokenHash]</db:value>
          <db:value key="created_at">NOW()</db:value>
          <db:value key="expires_at">DATE_ADD(NOW(), INTERVAL 24 HOUR)</db:value>
        </db:values>
      </db:insert>
    </mule:otherwise>
  </mule:choice>
</mule:flow>
```

#### Paso 4: Implementar Cleanup Job (2 horas)
```xml
<!-- Nueva tarea programada en Mule: -->
<flow name="token-cleanup-scheduler" doc:name="Token Cleanup Scheduler">
  <scheduler>
    <scheduling-strategy>
      <cron-expression>0 0 * * * ?</cron-expression> <!-- Cada hora -->
    </scheduling-strategy>
  </scheduler>
  
  <db:execute-script doc:name="Delete Expired Tokens">
    <db:sql>
      DELETE FROM json_web_token 
      WHERE expires_at < NOW() 
        OR (created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) AND is_valid = FALSE);
    </db:sql>
  </db:execute-script>
  
  <!-- Logging: -->
  <logger message="Token cleanup executed. Rows affected: #[payload]" level="INFO"/>
</flow>
```

#### Paso 5: Testing (1 hora)
```bash
# 1. Simular login 5 veces en 30 segundos con mismo usuario:
for i in {1..5}; do
  curl -X POST "https://api.mapfre.local/esp/ext/api/frontales/1.0/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "APP-CMPCRTVRDNSE", "password": "test123"}' \
    -w "HTTP %{http_code}\n"
  sleep 6  # Esperar 6 segundos entre intentos
done

# Esperado: HTTP 200 en todos (no duplicados en BD)

# 2. Verificar BD después:
mysql> SELECT COUNT(*) FROM json_web_token WHERE user_id = 'APP-CMPCRTVRDNSE';
-- Debería mostrar: 5 registros (1 activo + 4 expirados en próximas horas, O 1 si se retorna el mismo)
```

### Métricas de Éxito
- ✅ 0 errores de "Duplicate entry" en 24 horas
- ✅ Todos los logins retornan HTTP 200
- ✅ Base de datos sin tokens huérfanos
- ✅ Cleanup job ejecutándose sin errores

---

## 🟡 MEDIO: Identity Provider Not Found (1 ocurrencia)

### Descripción
El usuario APP-ESPsiiBDGI no puede autenticarse porque el Identity Provider 4d62b51ba425e99a4d043f792be91e00 no existe o está deshabilitado.

### Síntomas
```
[2026-06-08T16:23:13.416] INFO: ServerAuthenticationAssertion
could not verify identity provider ID 4d62b51ba425e99a4d043f792be91e00 
with credentials from APP-ESPsiiBDGI
Response: HTTP 401
```

### Plan de Corrección

#### Paso 1: Restaurar Identity Provider (15 min)
```bash
# En L7tech API Gateway Admin Console:
1. Ir a: Manage Identity Providers
2. Buscar ID: 4d62b51ba425e99a4d043f792be91e00
3. Si no existe:
   a. Ir a: Audit → Search for "4d62b51ba425e99a4d043f792be91e00"
   b. Ver cuándo fue eliminado (timestamp)
   c. Si fue accidental, contactar admin de backup
4. Si existe pero está disabled:
   a. Clic en "Edit"
   b. Cambiar "Enabled" a ✅
   c. Guardar cambios
5. Probar conectividad:
   - Para LDAP: Test LDAP Connection
   - Para Active Directory: Verify server binding
```

#### Paso 2: Verificar Configuración (20 min)
```bash
# En Admin Console:
1. Ir a: Manage Certificates
2. Buscar certificados de APP-ESPsiiBDGI
3. Verificar:
   - ✅ Certificado no expirado (Expiration date)
   - ✅ Certificado en trusted store
   - ✅ CN/Subject DN matches policy expectation
4. Ir a: Policies → siiFactEmIGIC
5. Revisar assertion: ServerAuthenticationAssertion
   - Verificar que el Identity Provider ID es correcto
   - Revisar los credential formats soportados
```

#### Paso 3: Reconfigurar Policy (30 min)
```xml
<!-- En siiFactEmIGIC policy: -->
<l7:Assertion>
  <ServerAuthenticationAssertion>
    <!-- Permitir múltiples providers como fallback -->
    <IdentityProviders>
      <!-- Provider primario -->
      <l7:Item id="4d62b51ba425e99a4d043f792be91e00">
        <l7:Name>Environment Active Directory</l7:Name>
        <l7:Enabled>true</l7:Enabled>
      </l7:Item>
      <!-- Provider de fallback -->
      <l7:Item id="backup-ldap-provider-id">
        <l7:Name>Backup LDAP Directory</l7:Name>
        <l7:Enabled>true</l7:Enabled>
      </l7:Item>
    </IdentityProviders>
    <!-- Usar variable para almacenar estado -->
    <VariableName>authentication.provider.used</VariableName>
  </ServerAuthenticationAssertion>
</l7:Assertion>
```

#### Paso 4: Testing (15 min)
```bash
# Realizar autenticación con certificado TLS:
curl -X GET "https://api.mapfre.local/esp/srv/sii/suministro-fact-emitidas" \
  --cert /path/to/APP-ESPsiiBDGI.crt \
  --key /path/to/APP-ESPsiiBDGI.key \
  --cacert /path/to/ca-bundle.crt

# Esperado: HTTP 200 (no 401)
```

### Métricas de Éxito
- ✅ APP-ESPsiiBDGI puede autenticarse sin errores
- ✅ 0 errores de "Identity Provider Not Found" en siguiente semana
- ✅ Tiempo de autenticación: < 100ms

---

## 🟡 MEDIO: JWT Token Validation Fallback (1 ocurrencia)

### Descripción
El servicio esp/srv/api/clients/1.0 falla en validación de JWT para APP-CMPAPPIAN pero logra recuperarse con OAuth2.

### Síntomas
```
[2026-06-08T16:21:14.530] WARNING: MAP IFW Validate JWT-v2.0
Error: "This token cannot be used with this service"
Response: HTTP 200 (recover via OAuth2)
```

### Plan de Corrección

#### Solución Recomendada (Consolidar JWT/OAuth2)
```xml
<!-- Consolidar en una sola política: MAP IFW Unified Token Validation -->
<mule:flow name="validate-token">
  <mule:choice>
    <!-- Primero intentar JWT -->
    <mule:when expression="payload.authHeader.startsWith('Bearer ')">
      <mule:try>
        <l7:ValidateJsonWebSignature>
          <l7:CheckExpiration>true</l7:CheckExpiration>
          <l7:ExtractClaims>true</l7:ExtractClaims>
        </l7:ValidateJsonWebSignature>
        <mule:success-response-handler>
          <logger message="JWT validation successful for #[payload.sub]" level="INFO"/>
        </mule:success-response-handler>
      </mule:try>
      <mule:error-handler>
        <mule:on-error-continue>
          <!-- Si JWT falla, intentar OAuth2 -->
          <logger message="JWT failed, falling back to OAuth2" level="WARN"/>
          <mule:flow-ref name="oauth2-validation-flow"/>
        </mule:on-error-continue>
      </mule:error-handler>
    </mule:when>
    <!-- Si no es JWT, usar OAuth2 directamente -->
    <mule:otherwise>
      <mule:flow-ref name="oauth2-validation-flow"/>
    </mule:otherwise>
  </mule:choice>
</mule:flow>

<!-- SubFlow para OAuth2 -->
<mule:sub-flow name="oauth2-validation-flow">
  <l7:OAuth2ProtectedResource>
    <!-- Configuración de OAuth2 -->
  </l7:OAuth2ProtectedResource>
</mule:sub-flow>
```

---

## 📊 Resumen de Implementación

| Error | Severidad | Tiempo | Esfuerzo | Owner |
|-------|-----------|--------|----------|-------|
| Azure Token | 🔴 CRÍTICO | 2.5h | 3 personas-h | Security Team |
| DB Duplicate | 🟠 ALTO | 3.25h | 4 personas-h | DB Admin + Dev |
| Identity Provider | 🟡 MEDIO | 1.25h | 1 persona-h | Auth Admin |
| JWT Fallback | 🟡 MEDIO | 1.5h | 2 personas-h | Dev Team |
| **TOTAL** | | **8.5h** | **10 personas-h** | Cross-team |

---

## 🔒 Rollback Strategy

Cada implementación tiene un plan de reversión:

1. **Git Branches**: Crear rama `hotfix/auth-errors-2026-06-08`
2. **Database Backups**: Snapshot antes de cualquier cambio
3. **Policy Versioning**: Mantener versiones anteriores de policies
4. **Monitoring**: Alertas configuradas para detectar regresión en < 5 minutos

---

## ✅ Validación Post-Implementación

Ejecutar después de completar todas las correcciones:

```bash
# 1. Ejecutar la suite de tests:
./run-api-tests.sh -env production -suite "error-recovery"

# 2. Verificar logs para errores recurrentes:
grep -i "azure token validation\|duplicate entry\|identity provider" /var/logs/l7tech/gateway.log

# 3. Monitorear dashboard:
- Error rate trending down
- Response times stable
- No nuevas excepciones

# 4. Validar con usuarios:
- APP-CMPCRTVRDNSE: Token login
- APP-CMPAPPIAN: API clients search
- APP-ESPsiiBDGI: SII reports
```

---

**Documento generado**: 2026-08-03  
**Versión**: 1.0  
**Próxima revisión**: Después de implementar correcciones
