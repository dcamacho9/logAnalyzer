#!/usr/bin/env python
"""
Script para verificar disponibilidad de Ollama y ejecutar el agente
"""

import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

def check_ollama():
    """Verificar si Ollama está disponible y qué modelos hay"""
    try:
        print("🔍 Verificando Ollama...")
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        models = [m['name'] for m in data.get('models', [])]
        
        if not models:
            print("❌ No hay modelos instalados en Ollama")
            print("\nDebes descargar un modelo. Ejecuta:")
            print("  ollama pull llama2")
            print("  ollama pull neural-chat")
            print("  ollama pull mistral")
            return False
            
        print("✅ Ollama está activo")
        print(f"\n📦 Modelos disponibles ({len(models)}):")
        for model in models:
            print(f"   - {model}")
        
        # Detectar el mejor modelo disponible
        preferred = ['mistral', 'neural-chat', 'llama2', 'llama']
        selected = None
        for pref in preferred:
            if any(pref in m.lower() for m in models):
                selected = next(m for m in models if pref in m.lower())
                break
        
        if not selected:
            selected = models[0]
        
        print(f"\n🚀 Usando modelo: {selected}")
        os.environ["OLLAMA_MODEL"] = selected
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a Ollama")
        print("   Asegúrate de ejecutar: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if not check_ollama():
        sys.exit(1)
    
    # Ejecutar el agente
    print("\n" + "="*60)
    print("Iniciando agente de análisis de logs...\n")
    from agent import main
    main()
