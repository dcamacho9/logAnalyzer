# 🚀 QUICK START: Comenzar Ahora

## ⚡ 3 Pasos (5 minutos)

### Paso 1️⃣ Reinicia el API

Abre PowerShell y ejecuta:

```powershell
cd "c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA\log-analyzer-agent"
python api.py
```

**Espera a ver esto:**
```
============================================================
 🚀 Iniciando API del Agente de Análisis de Logs
============================================================

📋 Endpoints disponibles:
  • GET  http://localhost:5000/api/health
  • POST http://localhost:5000/api/analyze
  • POST http://localhost:5000/api/patterns
  • POST http://localhost:5000/api/ollama/chat
  • POST http://localhost:5000/api/incidents
```

### Paso 2️⃣ Abre otra terminal PowerShell

### Paso 3️⃣ Ejecuta el test

```powershell
cd "c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA\log-analyzer-agent"
python quick_test_api.py
```

## ✅ Resultado Esperado

```
🧪 Prueba Rápida del API

============================================================

1️⃣  Health Check...
   ✅ API en línea

2️⃣  Análisis de Patrones...
   ✅ Éxito
   📋 36 eventos detectados
   🔍 X patrones identificados

3️⃣  Análisis Completo (con Ollama)...
   ✅ Análisis completado
   📊 Eventos: 36
   🤖 Respuesta Ollama:
      [respuesta del modelo...]

============================================================
✅ Prueba completada
```

## 🎉 ¡Listo!

Si ves `✅ Éxito` en los pasos 2 y 3, el problema está **SOLUCIONADO**.

## 📝 Ahora puedes usar el API así:

### Con Python

```python
import requests

# Leer tus logs
with open('test_logs2.txt', 'r') as f:
    logs = f.read()

# Hacer la petición
response = requests.post(
    'http://localhost:5000/api/analyze',
    json={
        "logs": logs,
        "limit": 100,
        "only_pattern_analysis": False
    },
    headers={'Content-Type': 'application/json; charset=utf-8'},
    timeout=60
)

# Ver resultado
print(response.json())
```

### Con cURL

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"logs":"...","limit":100}' \
  --max-time 60
```

### Con Postman

1. **POST** → `http://localhost:5000/api/analyze`
2. **Headers** → `Content-Type: application/json; charset=utf-8`
3. **Body** → raw JSON → tu payload
4. **Send**

## ❓ ¿Algo Salió Mal?

### Opción A: Aún hay error 400
- Reinicia el API
- Espera 3 segundos
- Intenta de nuevo

### Opción B: Timeout
- Es normal la primera vez
- Ollama está procesando
- Espera más y vuelve a intentar

### Opción C: Otro error
- Lee [API_400_ERROR_SOLUTION.md](API_400_ERROR_SOLUTION.md)
- Revisa los logs de la terminal del API
- Verifica que tu JSON sea válido

## 📚 Más Información

- **Resumen visual**: [CAMBIOS_APLICADOS_400_ERROR.md](CAMBIOS_APLICADOS_400_ERROR.md)
- **Guía completa**: [API_400_ERROR_SOLUTION.md](API_400_ERROR_SOLUTION.md)
- **Lista de cambios**: [LISTA_CAMBIOS_COMPLETA.md](LISTA_CAMBIOS_COMPLETA.md)
- **Troubleshooting**: [VERIFICAR_SOLUCION.md](VERIFICAR_SOLUCION.md)

## 🎯 Lo Importante

| Antes | Después |
|-------|---------|
| ❌ Error 400 | ✅ Funciona |
| ❌ Payloads >16MB rechazados | ✅ Hasta 100MB soportados |
| ❌ Errores genéricos | ✅ Errores informativos |
| ❌ Sin validación | ✅ Con validación |

## 🏁 Resumen

✅ **El error 400 ha sido solucionado**

✅ **El API ahora soporta payloads grandes**

✅ **Los errores son más informativos**

✅ **Todo está documentado**

¡Ahora puedes usar el API sin problemas! 🚀

---

**¿Preguntas?** Revisa la documentación o ejecuta `python quick_test_api.py`
