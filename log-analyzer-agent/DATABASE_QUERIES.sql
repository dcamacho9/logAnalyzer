-- ===============================================
-- MAPFRE API Gateway - Análisis y Monitoreo SQL
-- ===============================================
-- Base de datos: mapfre_gateway
-- Versión: 1.0
-- Fecha: 2026-08-03
-- ===============================================

-- =====================================================
-- SECCIÓN 1: DIAGNÓSTICO DE PROBLEMAS ACTUALES
-- =====================================================

-- 1.1: Ver todos los tokens duplicados de APP-CMPCRTVRDNSE
SELECT 
    token_id,
    user_id,
    created_at,
    expires_at,
    is_valid,
    COUNT(*) as ocurrencias
FROM json_web_token
WHERE user_id = 'APP-CMPCRTVRDNSE'
GROUP BY token_id, user_id, created_at
HAVING COUNT(*) > 1
ORDER BY created_at DESC;

-- 1.2: Tokens expirados que no han sido limpiados
SELECT 
    token_id,
    user_id,
    created_at,
    expires_at,
    DATEDIFF(NOW(), expires_at) as dias_expirado
FROM json_web_token
WHERE expires_at < NOW()
  AND is_valid = FALSE
ORDER BY expires_at DESC
LIMIT 50;

-- 1.3: Verificar integridad de base de datos
CHECK TABLE json_web_token;
ANALYZE TABLE json_web_token;
REPAIR TABLE json_web_token;

-- 1.4: Ver estadísticas de intentos de login fallidos
SELECT 
    DATE(created_at) as fecha,
    HOUR(created_at) as hora,
    COUNT(*) as intentos_login,
    SUM(CASE WHEN http_response = 200 THEN 1 ELSE 0 END) as exitosos,
    SUM(CASE WHEN http_response = 401 THEN 1 ELSE 0 END) as no_autorizados,
    SUM(CASE WHEN http_response = 500 THEN 1 ELSE 0 END) as errores_servidor
FROM api_gateway_logs
WHERE endpoint LIKE '%login%'
  AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY fecha, hora
ORDER BY fecha DESC, hora DESC;

-- =====================================================
-- SECCIÓN 2: LIMPIEZA Y MANTENIMIENTO
-- =====================================================

-- 2.1: Limpiar tokens expirados (seguro)
DELETE FROM json_web_token
WHERE expires_at < DATE_SUB(NOW(), INTERVAL 24 HOUR)
  AND is_valid = FALSE;

-- 2.2: Consolidar tokens duplicados - MANTENER EL MÁS RECIENTE
WITH tokens_a_eliminar AS (
    SELECT 
        token_id,
        user_id,
        ROW_NUMBER() OVER (PARTITION BY user_id, DATE(created_at) ORDER BY created_at DESC) as rn
    FROM json_web_token
    WHERE is_valid = TRUE
)
DELETE FROM json_web_token
WHERE token_id IN (
    SELECT token_id FROM tokens_a_eliminar WHERE rn > 1
);

-- 2.3: Limpiar registros de audit antiguos (> 90 días)
DELETE FROM audit_logs
WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
  AND event_type IN ('LOGIN_ATTEMPT', 'TOKEN_VALIDATION', 'AUTHENTICATION_FAILURE');

-- 2.4: Actualizar estadísticas de índices
OPTIMIZE TABLE json_web_token;
OPTIMIZE TABLE api_gateway_logs;
OPTIMIZE TABLE audit_logs;

-- =====================================================
-- SECCIÓN 3: VALIDACIÓN Y MONITOREO CONTINUO
-- =====================================================

-- 3.1: Dashboard de errores (últimas 24 horas)
SELECT 
    'Azure Token Validation' as error_type,
    COUNT(*) as count,
    MIN(timestamp) as first_occurrence,
    MAX(timestamp) as last_occurrence,
    COUNT(DISTINCT service_uuid) as affected_services,
    COUNT(DISTINCT client_ip) as affected_clients
FROM api_gateway_logs
WHERE log_level = 'WARNING'
  AND message LIKE '%Azure Token Validation%'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)

UNION ALL

SELECT 
    'Duplicate Primary Key',
    COUNT(*) as count,
    MIN(timestamp) as first_occurrence,
    MAX(timestamp) as last_occurrence,
    COUNT(DISTINCT service_id) as affected_services,
    COUNT(DISTINCT user_id) as affected_users
FROM api_gateway_logs
WHERE log_level = 'WARNING'
  AND message LIKE '%Duplicate entry%'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)

UNION ALL

SELECT 
    'Identity Provider Missing',
    COUNT(*) as count,
    MIN(timestamp) as first_occurrence,
    MAX(timestamp) as last_occurrence,
    COUNT(DISTINCT service_id) as affected_services,
    COUNT(DISTINCT user_id) as affected_users
FROM api_gateway_logs
WHERE log_level = 'WARNING'
  AND message LIKE '%could not verify identity provider%'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR);

-- 3.2: Rendimiento de autenticación por proveedor
SELECT 
    CASE 
        WHEN auth_method LIKE '%Azure%' THEN 'Azure AD'
        WHEN auth_method LIKE '%JWT%' THEN 'JWT'
        WHEN auth_method LIKE '%OAuth%' THEN 'OAuth2'
        WHEN auth_method LIKE '%Certificate%' THEN 'TLS Certificate'
        ELSE 'Other'
    END as auth_type,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN http_response = 200 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN http_response = 401 THEN 1 ELSE 0 END) as unauthorized,
    ROUND(
        (SUM(CASE WHEN http_response = 200 THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2
    ) as success_rate_percent,
    ROUND(AVG(response_time_ms), 2) as avg_response_time_ms
FROM api_gateway_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY auth_type
ORDER BY total_attempts DESC;

-- 3.3: Detectar patrones de reintento (indicativo de problemas)
SELECT 
    client_ip,
    user_id,
    COUNT(*) as request_count,
    COUNT(CASE WHEN http_response != 200 THEN 1 END) as failed_requests,
    MAX(timestamp) - MIN(timestamp) as time_span,
    ROUND(
        (COUNT(CASE WHEN http_response != 200 THEN 1 END) / COUNT(*)) * 100, 2
    ) as failure_rate_percent
FROM api_gateway_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY client_ip, user_id
HAVING COUNT(*) > 5 AND failure_rate_percent > 50
ORDER BY failure_rate_percent DESC;

-- =====================================================
-- SECCIÓN 4: ALERTAS Y THRESHOLDS
-- =====================================================

-- 4.1: Crear tabla para almacenar alertas generadas
CREATE TABLE IF NOT EXISTS error_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(100),
    error_message TEXT,
    affected_count INT,
    time_window VARCHAR(50),
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4.2: Procedimiento para generar alertas automáticas
DELIMITER //
CREATE PROCEDURE check_error_thresholds()
BEGIN
    DECLARE azure_errors INT;
    DECLARE db_errors INT;
    DECLARE provider_errors INT;
    
    -- Contar errores en última hora
    SELECT COUNT(*) INTO azure_errors
    FROM api_gateway_logs
    WHERE message LIKE '%Azure Token Validation%'
      AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
      AND log_level = 'WARNING';
    
    SELECT COUNT(*) INTO db_errors
    FROM api_gateway_logs
    WHERE message LIKE '%Duplicate entry%'
      AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
      AND log_level = 'WARNING';
    
    SELECT COUNT(*) INTO provider_errors
    FROM api_gateway_logs
    WHERE message LIKE '%could not verify identity provider%'
      AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
      AND log_level = 'WARNING';
    
    -- Generar alertas si se exceden thresholds
    IF azure_errors > 5 THEN
        INSERT INTO error_alerts (alert_type, error_message, affected_count, time_window, severity)
        VALUES ('AZURE_TOKEN', 'Azure Token Validation failures exceed threshold', azure_errors, '1h', 'CRITICAL');
    END IF;
    
    IF db_errors > 3 THEN
        INSERT INTO error_alerts (alert_type, error_message, affected_count, time_window, severity)
        VALUES ('DB_DUPLICATE', 'Duplicate Primary Key violations exceed threshold', db_errors, '1h', 'HIGH');
    END IF;
    
    IF provider_errors > 2 THEN
        INSERT INTO error_alerts (alert_type, error_message, affected_count, time_window, severity)
        VALUES ('PROVIDER_MISSING', 'Identity Provider failures exceed threshold', provider_errors, '1h', 'MEDIUM');
    END IF;
END //
DELIMITER ;

-- 4.3: Ejecutar verificación de alertas cada hora
-- (Agregar a cron job o scheduler externo)
-- CALL check_error_thresholds();

-- =====================================================
-- SECCIÓN 5: REPORTES DE TENDENCIAS
-- =====================================================

-- 5.1: Tendencia de errores últimos 7 días
SELECT 
    DATE(timestamp) as fecha,
    COUNT(*) as total_errors,
    SUM(CASE WHEN message LIKE '%Azure Token%' THEN 1 ELSE 0 END) as azure_errors,
    SUM(CASE WHEN message LIKE '%Duplicate entry%' THEN 1 ELSE 0 END) as db_errors,
    SUM(CASE WHEN message LIKE '%Identity provider%' THEN 1 ELSE 0 END) as provider_errors
FROM api_gateway_logs
WHERE log_level = 'WARNING'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(timestamp)
ORDER BY fecha DESC;

-- 5.2: Servicios más problemáticos
SELECT 
    service_name,
    COUNT(*) as error_count,
    COUNT(DISTINCT user_id) as affected_users,
    COUNT(DISTINCT client_ip) as affected_clients,
    ROUND(AVG(response_time_ms), 2) as avg_response_time,
    SUM(CASE WHEN http_response = 500 THEN 1 ELSE 0 END) as server_errors,
    SUM(CASE WHEN http_response = 401 THEN 1 ELSE 0 END) as auth_errors
FROM api_gateway_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND (http_response != 200 OR log_level = 'WARNING')
GROUP BY service_name
ORDER BY error_count DESC
LIMIT 20;

-- 5.3: Usuarios con más problemas de autenticación
SELECT 
    user_id,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN http_response = 200 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN http_response = 401 THEN 1 ELSE 0 END) as unauthorized,
    ROUND(
        (SUM(CASE WHEN http_response != 200 THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2
    ) as error_rate_percent,
    MAX(timestamp) as last_activity
FROM api_gateway_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY user_id
HAVING error_rate_percent > 20
ORDER BY total_attempts DESC;

-- =====================================================
-- SECCIÓN 6: ÍNDICES DE RENDIMIENTO
-- =====================================================

-- 6.1: Crear índices para queries comunes (mejorar performance)
CREATE INDEX idx_api_logs_timestamp ON api_gateway_logs(timestamp);
CREATE INDEX idx_api_logs_service_name ON api_gateway_logs(service_name);
CREATE INDEX idx_api_logs_user_id ON api_gateway_logs(user_id);
CREATE INDEX idx_api_logs_http_response ON api_gateway_logs(http_response);
CREATE INDEX idx_api_logs_message ON api_gateway_logs(message(255));
CREATE INDEX idx_jwt_user_valid ON json_web_token(user_id, is_valid, expires_at);

-- 6.2: Mostrar tamaño de tablas
SELECT 
    TABLE_NAME,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
    TABLE_ROWS as row_count
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'mapfre_gateway'
ORDER BY (data_length + index_length) DESC;

-- =====================================================
-- SECCIÓN 7: EXPORTAR DATOS PARA ANÁLISIS
-- =====================================================

-- 7.1: Exportar errores de las últimas 24 horas a archivo CSV
-- SELECT * FROM api_gateway_logs
-- WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
--   AND (http_response != 200 OR log_level = 'WARNING')
-- INTO OUTFILE '/tmp/mapfre_errors_24h.csv'
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n';

-- 7.2: Crear tabla temporal para análisis
CREATE TEMPORARY TABLE error_analysis_24h AS
SELECT 
    timestamp,
    service_name,
    user_id,
    client_ip,
    http_response,
    response_time_ms,
    message,
    log_level
FROM api_gateway_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
  AND (http_response != 200 OR log_level = 'WARNING');

SELECT COUNT(*) as total_errors FROM error_analysis_24h;

-- =====================================================
-- NOTAS DE IMPLEMENTACIÓN
-- =====================================================
/*
1. ANTES DE EJECUTAR CUALQUIER DELETE O UPDATE:
   - Hacer BACKUP completo de la base de datos
   - Ejecutar en DEV/QA primero
   - Validar resultados antes de producción

2. PROCEDURES Y EVENTOS:
   - check_error_thresholds() debe ejecutarse cada hora
   - Configurar como EVENT en MySQL:
   
   CREATE EVENT error_threshold_check
   ON SCHEDULE EVERY 1 HOUR
   DO CALL check_error_thresholds();

3. MONITOREO CONTINUO:
   - Ejecutar queries de tendencias diariamente
   - Revisar error_alerts tabla regularmente
   - Investigar variaciones > 50% en cualquier métrica

4. RETENCIÓN DE DATOS:
   - Mantener últimos 90 días en api_gateway_logs
   - Archivos antiguos en storage externo
   - Logs de auditoría: 1 año mínimo

5. PERFORMANCE:
   - Ejecutar OPTIMIZE después de limpieza masiva
   - Monitorear tamaño de json_web_token table
   - Reindex quarterly o cuando size > 1GB
*/
