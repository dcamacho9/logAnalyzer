#!/usr/bin/env python
"""
Interfaz Interactiva de Chat - Agente de Análisis de Logs
Permite conversar con el agente sobre logs en tiempo real
"""

import os
import json
import requests
from dotenv import load_dotenv
from skills.log_ingestion import fetch_logs
from skills.log_pattern_matcher import run_log_pattern_matcher

load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_API_URL}/api/generate"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "mistral:7b")

class LogAnalyzerChat:
    def __init__(self):
        self.logs = None
        self.pattern_result = None
        self.conversation_history = []
        
    def load_logs(self, limit=100):
        """Cargar logs desde la fuente de datos"""
        print("\n🔍 Cargando logs...")
        raw_log_lines = fetch_logs(source_id="prod-k8s-cluster", limit=limit)
        
        if not raw_log_lines:
            print("❌ No se recuperaron logs")
            return False
        
        print(f"✅ {len(raw_log_lines)} líneas de log cargadas")
        
        # Parsear y analizar patrones
        print("📊 Analizando patrones...")
        from agent import parse_log_lines
        self.logs = parse_log_lines(raw_log_lines)
        self.pattern_result = run_log_pattern_matcher(self.logs)
        
        print(f"✅ {len(self.pattern_result.get('annotated_events', []))} eventos anotados")
        return True
    
    def build_system_prompt(self):
        """Construir el system prompt con contexto de logs"""
        pattern_summary = self.pattern_result.get("pattern_summary", [])
        top_errors = self.pattern_result.get("top_errors", [])
        
        system_prompt = """Eres un Asistente Experto en Análisis de Logs e Infraestructura.
Tu rol es ayudar a los ingenieros de SRE/DevOps a diagnosticar problemas analizando logs.

CONTEXTO ACTUAL DE LOGS:
========================"""
        
        if pattern_summary:
            system_prompt += "\n\nRESUMEN DE PATRONES:\n"
            for pattern in pattern_summary[:5]:  # Primeros 5 patrones
                system_prompt += f"  - {pattern}\n"
        
        if top_errors:
            system_prompt += "\nERRORES MÁS FRECUENTES:\n"
            for error in top_errors[:5]:  # Top 5 errores
                system_prompt += f"  - {error['message']} ({error.get('count', 1)} ocurrencias)\n"
        
        system_prompt += """
INSTRUCCIONES:
- Responde basándote en los logs y patrones cargados
- Sé específico y técnico en tus análisis
- Si no tienes suficiente información, solicita más detalles
- Sugiere acciones remediales cuando sea posible
- Mantén respuestas concisas pero completas
"""
        return system_prompt
    
    def chat(self, user_message: str) -> str:
        """Enviar mensaje a Ollama y obtener respuesta"""
        # Agregar historial de conversación
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Construir prompt con historial
        system_prompt = self.build_system_prompt()
        
        # Formato de conversación para Ollama
        prompt = system_prompt + "\n\nCONVERSACIÓN:\n"
        
        for msg in self.conversation_history[-5:]:  # Últimos 5 mensajes
            if msg["role"] == "user":
                prompt += f"\nUsuario: {msg['content']}\n"
            else:
                prompt += f"Asistente: {msg['content']}\n"
        
        prompt += "\nAsistente:"
        
        try:
            response = requests.post(
                OLLAMA_GENERATE_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "num_predict": 500
                },
                timeout=300
            )
            response.raise_for_status()
            
            assistant_response = response.json().get("response", "").strip()
            
            # Guardar en historial
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            return assistant_response
            
        except requests.exceptions.ConnectionError:
            return "❌ Error: No se puede conectar a Ollama. ¿Está ejecutándose 'ollama serve'?"
        except requests.exceptions.Timeout:
            return "⏱️ Timeout: Ollama tardó demasiado. Intenta con una pregunta más corta."
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def show_help(self):
        """Mostrar comandos disponibles"""
        print("\n" + "="*60)
        print("COMANDOS DISPONIBLES")
        print("="*60)
        print("/help         - Mostrar esta ayuda")
        print("/stats        - Ver estadísticas de logs")
        print("/patterns     - Mostrar patrones detectados")
        print("/errors       - Mostrar errores principales")
        print("/reload       - Recargar logs")
        print("/history      - Ver historial de conversación")
        print("/clear        - Limpiar historial")
        print("/exit         - Salir")
        print("\nO escribe tu pregunta naturalmente para analizar los logs")
        print("="*60 + "\n")
    
    def show_stats(self):
        """Mostrar estadísticas de logs"""
        if not self.logs:
            print("❌ No hay logs cargados")
            return
        
        print("\n" + "="*60)
        print("ESTADÍSTICAS DE LOGS")
        print("="*60)
        print(f"Total de eventos: {len(self.logs)}")
        
        levels = {}
        for log in self.logs:
            level = log.get("level", "UNKNOWN")
            levels[level] = levels.get(level, 0) + 1
        
        print("\nDistribución por nivel:")
        for level, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.logs)) * 100
            print(f"  {level:12} {count:5} ({percentage:5.1f}%)")
        print("="*60 + "\n")
    
    def show_patterns(self):
        """Mostrar patrones detectados"""
        if not self.pattern_result:
            print("❌ No hay análisis de patrones")
            return
        
        patterns = self.pattern_result.get("pattern_summary", [])
        print("\n" + "="*60)
        print("PATRONES DETECTADOS")
        print("="*60)
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. {pattern}")
        print("="*60 + "\n")
    
    def show_errors(self):
        """Mostrar errores principales"""
        if not self.pattern_result:
            print("❌ No hay análisis de errores")
            return
        
        errors = self.pattern_result.get("top_errors", [])
        print("\n" + "="*60)
        print("ERRORES PRINCIPALES")
        print("="*60)
        for i, error in enumerate(errors[:10], 1):
            count = error.get("count", 1)
            message = error.get("message", "Unknown")
            print(f"{i:2}. [{count:3}x] {message[:70]}")
        print("="*60 + "\n")

def main():
    print("\n" + "="*60)
    print("🤖 AGENTE IA - ANALIZADOR DE LOGS INTERACTIVO")
    print("="*60)
    
    # Inicializar chat
    chat = LogAnalyzerChat()
    
    # Cargar logs automáticamente
    if not chat.load_logs():
        return
    
    print("\n✅ Sistema listo. Escribe /help para ver comandos o haz una pregunta")
    print("-"*60 + "\n")
    
    # Loop interactivo
    while True:
        try:
            user_input = input("📝 Tú: ").strip()
            
            if not user_input:
                continue
            
            # Comandos especiales
            if user_input.lower() == "/exit":
                print("\n👋 ¡Hasta luego!")
                break
            elif user_input.lower() == "/help":
                chat.show_help()
            elif user_input.lower() == "/stats":
                chat.show_stats()
            elif user_input.lower() == "/patterns":
                chat.show_patterns()
            elif user_input.lower() == "/errors":
                chat.show_errors()
            elif user_input.lower() == "/reload":
                print("\n🔄 Recargando logs...")
                if chat.load_logs():
                    print("✅ Logs recargados exitosamente\n")
                else:
                    print("❌ Error al recargar logs\n")
            elif user_input.lower() == "/history":
                print("\n📜 HISTORIAL DE CONVERSACIÓN")
                print("="*60)
                for msg in chat.conversation_history:
                    role = "👤 Usuario" if msg["role"] == "user" else "🤖 Asistente"
                    print(f"{role}: {msg['content'][:100]}...")
                print("="*60 + "\n")
            elif user_input.lower() == "/clear":
                chat.conversation_history = []
                print("✅ Historial limpiado\n")
            else:
                # Procesar como pregunta normal
                print("\n🤖 Analizando...\n")
                response = chat.chat(user_input)
                print(f"🤖 Asistente: {response}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()
