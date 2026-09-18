#!/usr/bin/env python3
"""
Cliente mejorado para probar el endpoint /api/analyze
"""

import json
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_api():
    """Prueba el API con manejo robusto de payloads"""
    
    # Leer logs desde el archivo de prueba
    test_logs_path = Path("test_logs2.txt")
    if not test_logs_path.exists():
        print(f"❌ Archivo {test_logs_path} no encontrado")
        return
    
    with open(test_logs_path, 'r', encoding='utf-8') as f:
        logs_content = f.read()
    
    print(f"📊 Tamaño de logs: {len(logs_content)} caracteres")
    print(f"📍 URL del API: {BASE_URL}\n")
    
    # Test 1: Health Check
    print("=" * 70)
    print("TEST 1: Health Check")
    print("=" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n")
    
    # Test 2: Análisis solo de patrones (más rápido)
    print("=" * 70)
    print("TEST 2: Análisis de Patrones (sin Ollama)")
    print("=" * 70)
    
    payload = {
        "logs": logs_content,
        "limit": 100,
        "only_pattern_analysis": True
    }
    
    payload_size = len(json.dumps(payload))
    print(f"📦 Tamaño del payload: {payload_size:,} bytes (~{payload_size/1024:.1f} KB)")
    print(f"📝 Líneas de logs: {len(logs_content.split(chr(10)))}")
    
    headers = {
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    try:
        print(f"\n⏳ Enviando petición a {BASE_URL}/api/patterns...")
        start = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/patterns",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        elapsed = time.time() - start
        
        print(f"✅ Respuesta recibida en {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estado: {data.get('status')}")
            print(f"📋 Eventos anotados: {len(data.get('annotated_events', []))}")
            print(f"🔍 Patrones identificados: {len(data.get('pattern_summary', []))}")
            print(f"⚠️  Errores encontrados: {len(data.get('top_errors', []))}")
            
            # Mostrar muestra de eventos
            if data.get('annotated_events'):
                print(f"\n📌 Primeros eventos:")
                for event in data.get('annotated_events', [])[:3]:
                    print(f"  • {event}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
    
    except requests.exceptions.Timeout:
        print(f"❌ Timeout después de 30 segundos")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n")
    
    # Test 3: Análisis completo con Ollama
    print("=" * 70)
    print("TEST 3: Análisis Completo (con Ollama)")
    print("=" * 70)
    
    payload_full = {
        "logs": logs_content,
        "limit": 100,
        "only_pattern_analysis": False
    }
    
    try:
        print(f"⏳ Enviando petición a {BASE_URL}/api/analyze...")
        start = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=payload_full,
            headers=headers,
            timeout=60
        )
        
        elapsed = time.time() - start
        
        print(f"✅ Respuesta recibida en {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estado: {data.get('status')}")
            print(f"📈 Paso: {data.get('step')}")
            print(f"📊 Eventos procesados: {data.get('total_events_processed')}")
            print(f"\n📝 Reporte de Diagnóstico:")
            print(data.get('diagnostic_report', 'N/A')[:500])
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
    
    except requests.exceptions.Timeout:
        print(f"⚠️  Timeout después de 60 segundos (Ollama puede estar tardando)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Pruebas completadas")
    print("=" * 70)

if __name__ == "__main__":
    test_api()
