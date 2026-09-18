FROM ollama/ollama:latest
# Instalar Python (u otro lenguaje que use tu agente)RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app
# Copiar requerimientos y código del agenteCOPY requirements.txt .RUN pip3 install --no-cache-dir -r requirements.txtCOPY . .
# Exponer el puerto por defecto de Ollama y el de tu agenteEXPOSE 11434EXPOSE 8080# Usar un script de inicio para arrancar Ollama y el agente simultáneamenteRUN chmod +x start.shCMD ["./start.sh"]