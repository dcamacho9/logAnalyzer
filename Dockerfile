FROM ollama/ollama:latest

# Exponer el puerto por defecto de Ollama
EXPOSE 11434

# Configurar variables de entorno indispensables
ENV OLLAMA_HOST=0.0.0.0

# Truco para descargar el modelo durante la construcción de la imagen
RUN (ollama serve &) && sleep 5 && ollama pull llama3.2:1b
