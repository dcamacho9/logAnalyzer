# ⚡ VERIFICACIÓN RÁPIDA: Error 400 Solucionado

## 🎯 En 3 Pasos

### Paso 1: Reinicia el API
```powershell
cd "c:\Users\dcamachoj\Desktop\Agente Trazas OLLAMA\log-analyzer-agent"
python api.py
```

Deberías ver:
```
============================================================
 🚀 Iniciando API del Agente de Análisis de Logs
============================================================
```

### Paso 2: Abre una nueva terminal PowerShell

### Paso 3: Ejecuta el test
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
      ...

============================================================
✅ Prueba completada
```

## ❌ Si ves un error

**Opción A: Error 400 aún presente**
- Verifica que reiniciaste el API
- Espera 3 segundos después de reiniciar
- Intenta de nuevo

**Opción B: Timeout**
- Es normal si es la primera vez
- Ollama está procesando la solicitud
- Espera y vuelve a intentar

**Opción C: Otro error**
- Copia el error y búscalo en `API_400_ERROR_SOLUTION.md`
- Mira los logs de la terminal del API

## 🔍 Test Manual con cURL

Si prefieres verificar manualmente:

```powershell
# Test 1: Health check
curl http://localhost:5000/api/health

# Esperado:
# {"status":"OK","service":"Log Analyzer Agent",...}

# Test 2: Patrones con logs pequeño
curl -X POST http://localhost:5000/api/patterns `
  -H "Content-Type: application/json" `
  -d '{"logs":"INFO Line 1\nINFO Line 2", "only_pattern_analysis":true}'

# Esperado: Status 200 (no 400)
```

## 📝 Test Manual con Python

```python
# test_manual.py
import requests

# Test 1
print("Test 1: Health Check")
r = requests.get("http://localhost:5000/api/health")
print(f"Status: {r.status_code}")
print(f"OK\n" if r.status_code == 200 else "ERROR\n")

# Test 2
print("Test 2: Análisis de Patrones")
with open('test_logs2.txt', 'r') as f:
    logs = f.read()

r = requests.post(
    "http://localhost:5000/api/patterns",
    json={"logs": logs},
    headers={'Content-Type': 'application/json; charset=utf-8'},
    timeout=15
)
print(f"Status: {r.status_code}")
print(f"OK - {len(r.json().get('annotated_events', []))} eventos\n" if r.status_code == 200 else f"ERROR\n")

# Test 3
print("Test 3: Análisis Completo")
r = requests.post(
    "http://localhost:5000/api/analyze",
    json={"logs": logs, "only_pattern_analysis": False},
    headers={'Content-Type': 'application/json; charset=utf-8'},
    timeout=60
)
print(f"Status: {r.status_code}")
print(f"OK\n" if r.status_code == 200 else f"ERROR\n")

print("✅ Todos los tests completados")
```

Guarda como `test_manual.py` y ejecuta:
```bash
python test_manual.py
```

## 📋 Qué Se Cambió

1. **api.py** - Configuración de Flask aumentada
2. **api.py** - Mejor manejo de errores JSON
3. **api.py** - Validación de tipos de datos
4. **TODOS los endpoints** - Parseo JSON mejorado

Ver: [CAMBIOS_APLICADOS_400_ERROR.md](CAMBIOS_APLICADOS_400_ERROR.md)

## 🎉 Si Todo Funciona

¡Felicidades! El error 400 ha sido solucionado.

Ahora puedes:
- ✅ Enviar logs grandes sin error 400
- ✅ Recibir análisis de patrones en ~2-5 segundos
- ✅ Recibir diagnóstico completo en ~20-60 segundos
- ✅ Ver errores más informativos si algo falla

## 📞 Si Algo No Funciona

1. Lee [API_400_ERROR_SOLUTION.md](API_400_ERROR_SOLUTION.md)
2. Revisa los logs de la terminal del API
3. Verifica que el Content-Type sea correcto
4. Aumenta el timeout en tus requests

¡Eso es todo! 🚀
