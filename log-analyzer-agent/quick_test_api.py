#!/usr/bin/env python3
"""
Script para probar rápidamente si el error 400 se ha solucionado
"""

import json
import requests
from pathlib import Path

BASE_URL = "http://localhost:5000"
LOGS_FILE = "test_logs2.txt"

def main():
    # Verificar que el archivo existe
    if not Path(LOGS_FILE).exists():
        print(f"❌ Error: {LOGS_FILE} no encontrado")
        return
    
    # Leer logs
    with open(LOGS_FILE, 'r', encoding='utf-8') as f:
        logs = f.read()
    
    print("🧪 Prueba Rápida del API\n")
    print("=" * 60)
    
    # Test 1: Health
    print("\n1️⃣  Health Check...")
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=3)
        if r.status_code == 200:
            print("   ✅ API en línea")
        else:
            print(f"   ❌ Status: {r.status_code}")
            return
    except Exception as e:
        print(f"   ❌ No se puede conectar: {e}")
        return
    
    # Test 2: Patrón analysis
    print("\n2️⃣  Análisis de Patrones...")
    payload = {
        "logs": logs,
        "only_pattern_analysis": True
    }
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/patterns",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if r.status_code == 200:
            data = r.json()
            events = len(data.get('annotated_events', []))
            patterns = len(data.get('pattern_summary', []))
            print(f"   ✅ Éxito")
            print(f"   📋 {events} eventos detectados")
            print(f"   🔍 {patterns} patrones identificados")
        else:
            print(f"   ❌ Status {r.status_code}: {r.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Timeout (API tardando)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Full analysis
    print("\n3️⃣  Análisis Completo (con Ollama)...")
    payload['only_pattern_analysis'] = False
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/analyze",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Análisis completado")
            print(f"   📊 Eventos: {data.get('total_events_processed')}")
            print(f"   🤖 Respuesta Ollama:")
            resp = data.get('diagnostic_report', '')[:300]
            for line in resp.split('\n'):
                print(f"      {line}")
        else:
            print(f"   ❌ Status {r.status_code}: {r.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Timeout (espera más, Ollama está procesando...)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Prueba completada\n")

if __name__ == "__main__":
    main()
