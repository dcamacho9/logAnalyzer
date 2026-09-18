#!/usr/bin/env python3
"""
Script para probar el endpoint /api/analyze con diferentes tamaños de payload
y verificar dónde está el problema
"""

import json
import requests
from pathlib import Path

BASE_URL = "http://localhost:5000"

# Leer logs desde el archivo de prueba
test_logs_path = Path("test_logs2.txt")
if not test_logs_path.exists():
    print(f"❌ Archivo {test_logs_path} no encontrado")
    exit(1)

with open(test_logs_path, 'r', encoding='utf-8') as f:
    logs_content = f.read()

print(f"📊 Tamaño de logs: {len(logs_content)} caracteres")
print(f"📍 URL del API: {BASE_URL}\n")

# Test 1: Verificar salud
print("=" * 60)
print("TEST 1: Verificar salud del API")
print("=" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")
    exit(1)

# Test 2: Probar con payload pequeño (primeras 5 líneas)
print("=" * 60)
print("TEST 2: Payload pequeño (primeras 5 líneas)")
print("=" * 60)
lines = logs_content.split('\n')[:5]
small_payload = {
    "logs": '\n'.join(lines),
    "limit": 5,
    "only_pattern_analysis": True
}
print(f"Tamaño del payload: {len(json.dumps(small_payload))} bytes")
try:
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json=small_payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 3: Probar con payload grande (todos los logs)
print("=" * 60)
print("TEST 3: Payload grande (todos los logs)")
print("=" * 60)
large_payload = {
    "logs": logs_content,
    "limit": 100,
    "only_pattern_analysis": True
}
payload_size = len(json.dumps(large_payload))
print(f"Tamaño del payload: {payload_size} bytes (~{payload_size/1024:.1f} KB)")

try:
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json=large_payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Response: {response.text}\n")
    else:
        print(f"✅ Response: {response.text[:500]}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 4: Intentar con request.data directamente (raw)
print("=" * 60)
print("TEST 4: Raw JSON string")
print("=" * 60)
raw_json = json.dumps(large_payload, ensure_ascii=False)
try:
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        data=raw_json,
        headers={'Content-Type': 'application/json; charset=utf-8'},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Response: {response.text}\n")
    else:
        print(f"✅ Response: {response.text[:500]}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

print("=" * 60)
print("✅ Pruebas completadas")
print("=" * 60)
