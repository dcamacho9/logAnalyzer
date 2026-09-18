"""
Orquestador Central del Agente de Análisis de Logs e Incidentes ServiceNow.
Usa Ollama para el análisis cognitivo y Python para la ejecución de Skills.
"""

import os
import json
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

# Importar las habilidades del directorio local skills/
from skills.log_ingestion import fetch_logs
from skills.log_pattern_matcher import run_log_pattern_matcher
from skills.servicenow_token_generator import run_servicenow_token_generator
from skills.servicenow_incident_creator import run_servicenow_incident_creator

# Cargar variables de entorno desde el archivo .env si existe (útil en desarrollo local)
load_dotenv()

# =====================================================
# LIMPIEZA DE TEXTO (NUEVO)
# =====================================================
def clean_text_response(text: str) -> str:
    """
    Limpia caracteres especiales y no imprimibles del texto
    - Convierte secuencias escape literales (\\n, \\r, \\t) a caracteres reales
    - Remueve caracteres de control no imprimibles
    - Normaliza espacios en blanco múltiples
    - Limpia caracteres especiales problemáticos
    """
    if not text:
        return text
    
    # Convertir secuencias escape literales a caracteres reales
    # (ej: "\n" string literal -> \n real)
    text = text.replace('\\n', '\n')
    text = text.replace('\\r', '\r')
    text = text.replace('\\t', '\t')
    text = text.replace('\\"', '"')
    
    # Remover caracteres de control no imprimibles (excepto \n, \r, \t)
    # Rango de caracteres imprimibles: 32-126 en ASCII
    text = ''.join(
        char for char in text 
        if ord(char) >= 32 or char in '\n\r\t'
    )
    
    # Reemplazar múltiples espacios en blanco con un único espacio (solo en línea, no saltos)
    lines = text.split('\n')
    lines = [re.sub(r' +', ' ', line) for line in lines]
    text = '\n'.join(lines)
    
    # Remover espacios en blanco al inicio y final de líneas
    text = '\n'.join(line.strip() for line in text.split('\n'))
    
    # Remover líneas completamente vacías múltiples (pero preservar saltos de línea simples)
    text = re.sub(r'\n\n+', '\n\n', text)
    
    return text.strip()

def parse_log_lines(raw_lines: list) -> list:
    """Convierte líneas de log en strings a diccionarios estructurados."""
    parsed_events = []
    
    for line in raw_lines:
        if not line.strip():
            continue
            
        # Intenta extraer timestamp y nivel usando regex
        # Formato esperado: 2026-07-31T09:40:01Z [LEVEL] Mensaje...
        match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+\[(\w+)\]\s+(.*)', line)
        
        if match:
            timestamp, level, message = match.groups()
            parsed_events.append({
                "timestamp": timestamp,
                "level": level.upper(),
                "message": message,
                "rawLine": line,
                "service": "unknown"  # Campo requerido por log_pattern_matcher
            })
        else:
            # Fallback para líneas que no coinciden con el formato esperado
            parsed_events.append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "UNKNOWN",
                "message": line,
                "rawLine": line,
                "service": "unknown"
            })
    
    return parsed_events

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_API_URL}/api/generate"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "MODEL_NAME")  # Usa variable de entorno o por defecto phi:2.7b (mas rapido)

def get_available_models() -> list:
    """Obtiene la lista de modelos disponibles en Ollama"""
    try:
        response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        return [m['name'] for m in data.get('models', [])]
    except Exception:
        return []

def call_ollama(prompt_content: str) -> str:
    """Envía el contenido estructurado al agente compilado en Ollama."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_content,
        "stream": False  # Cambiar a True si deseas procesar la respuesta en streaming
    }
    
    try:
        print(f"[*] Enviando solicitud a Ollama ({MODEL_NAME})... esto puede tomar varios minutos.")
        response = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=900)  # Aumentado a 15 minutos
        response.raise_for_status()
        response_text = response.json().get("response", "")
        # Limpiar caracteres especiales
        response_text = clean_text_response(response_text)
        return response_text
    except requests.exceptions.Timeout:
        print("\n> [!CAUTION]")
        print("> **Timeout de Conexión**: Ollama tardó demasiado en responder (>5 minutos).")
        print("> Esto puede ocurrir si el modelo está usando CPU en lugar de GPU.")
        print("> Considera usar un modelo más pequeño (ej: mistral:7b) o esperar a que se complete.")
        return ""
    except requests.exceptions.ConnectionError:
        print("\n> [!CAUTION]")
        print("> **Error de Infraestructura**: No se pudo conectar con Ollama. ¿Está ejecutándose `ollama serve`?")
        return ""
    except Exception as e:
        print(f"\nError al comunicarse con Ollama: {e}")
        return ""

def main():
    print("=" * 60)
    print(" Creando Sesión de Diagnóstico Automático e Integración ITSM ")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # STEP 1: Ingesta de Logs (Skill 1)
    # -------------------------------------------------------------------------
    print("\n[1/4] Ingestando trazas desde la fuente de datos...")
    # Parámetros de ejemplo para la ingesta (pueden venir de argumentos de consola)
    raw_log_lines = fetch_logs(source_id="prod-k8s-cluster", limit=100)
    
    if not raw_log_lines:
        print("[-] No se recuperaron logs. Abortando pipeline.")
        return
    
    # Parsear las líneas de log a diccionarios estructurados
    raw_logs = parse_log_lines(raw_log_lines)

    # -------------------------------------------------------------------------
    # STEP 2: Análisis Sintáctico y Extracción de Patrones (Skill 2)
    # -------------------------------------------------------------------------
    print("[2/4] Ejecutando log-pattern-matcher (Clasificación por Regex y PII)...")
    pattern_result = run_log_pattern_matcher(raw_logs)
    annotated_events = pattern_result.get("annotated_events", [])
    correlation_data = {"pattern_summary": pattern_result.get("pattern_summary", []), "top_errors": pattern_result.get("top_errors", [])}
    
    # Construir el prompt para Ollama con los eventos pre-procesados
    prompt_for_llm = f"""
    Analice los siguientes eventos anotados y genere el Reporte Diagnóstico Causa-Raíz.
    
    Eventos Anotados (JSON):
    {json.dumps(annotated_events, indent=2)}
    
    Datos de Correlación:
    {json.dumps(correlation_data, indent=2)}
    """

    # -------------------------------------------------------------------------
    # STEP 3: Inferencia en Ollama (Generación del Reporte Diagnóstico - Skill 3)
    # -------------------------------------------------------------------------
    print("[3/4] Invocando inteligencia local en Ollama para diagnóstico causa-raíz...")
    diagnostic_report = call_ollama(prompt_for_llm)
    
    if not diagnostic_report:
        print("[-] Falló la generación del diagnóstico.")
        return
        
    # Imprimir el reporte de diagnóstico en la consola (Markdown)
    print("\n" + "=" * 20 + " REPORTE DIAGNÓSTICO " + "=" * 20)
    print(diagnostic_report)
    print("=" * 61 + "\n")

    # -------------------------------------------------------------------------
    # STEP 4: Integración Operacional con ServiceNow (Skills 4 y 5)
    # -------------------------------------------------------------------------
    print("[4/4] Inicializando pasarela operacional ServiceNow...")
    
    # 4.1 Generar/Validar Token OAuth 2.0 (Skill 5)
    auth_result = run_servicenow_token_generator()
    
    if auth_result["status"] == "BLOCKED":
        print("\n> [!CAUTION]")
        print(f"> **Acción Requerida**: {auth_result['reason']}")
        print("> Configure las variables de entorno en su sesión de terminal para habilitar la creación de tickets.")
        return
        
    elif auth_result["status"] == "RECOMMENDED":
        print(f"\n> [!WARNING] Advertencia de Seguridad: {auth_result['reason']}")
    
    # Mostrar bloque informativo del Token obtenido de manera segura
    token_data = auth_result["report_data"]
    print("\n## ServiceNow Token")
    print(f"| Field | Value |")
    print(f"|-------|-------|")
    print(f"| Instance | {token_data['instance']} |")
    print(f"| Token type | Bearer |")
    print(f"| Expires at (UTC) | {token_data['expires_at']} |")
    print(f"| Stored in | `$env:SERVICENOW_ACCESS_TOKEN` |")
    print(f"| Next step | Use token in `Authorization: Bearer ****{token_data['last4']}` header |")
    print("-" * 60)

    # 4.2 Si el token es válido y la creación de incidentes está activa, abrir los tickets (Skill 4)
    # El creador lee internamente el token inyectado en os.environ
    if os.environ.get("SERVICENOW_CREATE_INCIDENTS", "false").lower() == "true":
        print("\nProcesando apertura automatizada de incidentes...")
        incident_result = run_servicenow_incident_creator(
            annotated_events=annotated_events,
            correlation_data=correlation_data,
            dedup_mode="pattern",
            log_source="prod-k8s-cluster",
            time_range="Últimos 15 minutos"
        )
        
        if incident_result["status"] in ["OK", "INFO"]:
            incidents = incident_result.get("incidents", [])
            stats = incident_result.get("stats", {})
            
            if not incidents:
                print(f"\nINFO: {incident_result['reason']}")
                return

            # Renderizar tabla contractual de incidentes procesados
            print("\n## ServiceNow Incidents Created\n")
            print("| # | Incident | Urgency | Pattern Type | Service | First Occurrence |")
            print("|---|------------|-------------|--------------|----------|--------------------------|")
            for idx, inc in enumerate(incidents, 1):
                # Si es un duplicado omitido, ajustar visualmente la urgencia
                urgency_str = inc['urgency']
                ticket_number = inc['number']
                if inc.get("isDuplicate"):
                    ticket_number = f"{ticket_number} (Duplicate)"
                
                print(f"| {idx} | {ticket_number} | {urgency_str} | {inc['patternType']} | {inc['service']} | {inc['firstOccurrence']} |")
            
            # Renderizar Telemetría Operacional
            print("\n---\n")
            print("> **Operational Telemetry Summary**")
            print(f"> - **Dedup mode**: {stats.get('dedupMode')}")
            print(f"> - **Total ERROR events processed**: {stats.get('totalErrorsProcessed')}")
            print(f"> - **Incident groups created**: {stats.get('groupsCreated')}")
            print(f"> - **Duplicates skipped**: {stats.get('duplicatesSkipped')}")
            print("\n---")
        else:
            print(f"\n[-] Error al procesar incidentes: {incident_result.get('reason')}")
    else:
        print("\nINFO: La variable `SERVICENOW_CREATE_INCIDENTS` está en 'false'. No se crearon tickets en la plataforma.")

if __name__ == "__main__":
    main()