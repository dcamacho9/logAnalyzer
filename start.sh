#!/bin/bash
 
# Iniciar Ollama en segundo plano
ollama serve &
 
# Esperar a que Ollama responda
sleep 5
 
# Descargar el modelo deseado (ej. llama3, phi3, deepseek-r1, etc.)
echo "Descargando el modelo..."
ollama pull llama3
 
# Arrancar la aplicación de tu agente de IA (ej. un backend en FastAPI o Flask)
echo "Iniciando el Agente de IA..."
python3 api_optimized.py