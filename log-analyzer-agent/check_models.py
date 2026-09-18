#!/usr/bin/env python
"""
Script para verificar modelos disponibles en Ollama
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434"

try:
    print("🔍 Consultando modelos disponibles en Ollama...\n")
    response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    response.raise_for_status()
    
    data = response.json()
    models = data.get('models', [])
    
    if not models:
        print("❌ No hay modelos instalados.")
        print("\nDebes descargar al menos uno. Ejecuta en otra terminal:")
        print("  ollama pull llama2")
        print("  ollama pull neural-chat")
        print("  ollama pull mistral")
        exit(1)
    
    print(f"✅ {len(models)} modelo(s) disponible(s):\n")
    for model in models:
        name = model['name']
        size = model.get('size', 0) / (1024**3)  # Convertir a GB
        print(f"  📦 {name:<30} ({size:.1f} GB)")
    
    print("\n✨ Modelos recomendados para este agente:")
    print("  1. mistral (rápido, ~4GB)")
    print("  2. neural-chat (rápido, ~4GB)")  
    print("  3. llama2 (estable, ~3.8GB)")
    
except requests.exceptions.ConnectionError:
    print("❌ No se puede conectar a Ollama en http://localhost:11434")
    print("   Ejecuta en una terminal: ollama serve")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
