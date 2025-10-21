## Voice Agent (ASR → LLM → TTS)

Servicio FastAPI que recibe audio (.wav/.mp3), lo transcribe (ASR directo a Azure), analiza el texto con un LLM (LangChain + Azure OpenAI) y devuelve audio sintetizado (TTS con Azure), junto con un JSON con la transcripción y la respuesta textual.

### Características
- ASR: consumo directo del endpoint de Azure OpenAI Audio Transcriptions (multipart: model + file).
- NLP: LangChain con `AzureChatOpenAI` (deployment configurable).
- TTS: consumo directo del endpoint de Azure OpenAI Audio Speech (JSON body: model, input, voice).
- Observabilidad: logging estructurado, `x-request-id` en todas las respuestas, y soporte opcional para Application Insights (Azure Monitor).
- Manejo de errores: respuestas consistentes con `{"detail": "..."}` y códigos HTTP 4xx/5xx apropiados.
- FastAPI con OpenAPI/Swagger.
- Dockerfile para contenedorización.
- CI/CD: workflow de GitHub Actions para construir y desplegar contenedor a Azure Web App (container).

### Arquitectura (alto nivel)
```
Audio (.wav/.mp3) → [ASR REST] → Texto → [LLM LangChain + Azure OpenAI] → Respuesta texto → [TTS REST] → Audio (base64)
```

### Estructura de carpetas
- `app/`
  - `app.py` — App FastAPI, CORS, health, request-id middleware, handlers globales.
  - `config.py` — Variables de entorno (pydantic-settings).
  - `routers/voice.py` — Endpoint POST `/v1/voice` (pipeline ASR → LLM → TTS).
  - `services/`
    - `asr.py` — Azure Audio Transcriptions (REST, multipart).
    - `nlp.py` — LLM con LangChain + AzureChatOpenAI.
    - `tts.py` — Azure Audio Speech (REST, binario → base64).
- `tests/` — Pruebas (salud y flujo de voz con stub).
- `.github/workflows/main_savanttest.yml` — Build+Push a ACR y deploy a Azure Web App container.
- `Dockerfile` — Imagen lista para producción.

### Requisitos
- Python 3.11+
- Variables de entorno en `.env` (no lo subas al repo)

## Configuración (.env)
Variables principales por componente (usa valores propios):

### General (LLM)
- `AZURE_OPENAI_API_KEY=<clave>`
- `AZURE_INFERENCE_ENDPOINT=<url>` (opcional). Si está presente, se derivan `AZURE_OPENAI_ENDPOINT` y `AZURE_OPENAI_DEPLOYMENT`.
- `AZURE_OPENAI_ENDPOINT=<url>` (opcional si no usas el anterior)
- `AZURE_OPENAI_DEPLOYMENT=<nombre>` (opcional si no usas el anterior)
- `LLM_MODEL=gpt-4o` (fallback de deployment), `LLM_TEMPERATURE=0.3`, `LLM_MAX_TOKENS=1024`

### ASR (Audio Transcriptions)
- `AZURE_AUDIO_TRANSCRIBE_ENDPOINT=https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>/audio/transcriptions?api-version=<ver>`
- `AZURE_AUDIO_TRANSCRIBE_MODEL=gpt-4o-mini-transcribe`
- `AZURE_AUDIO_API_KEY=<clave>` (si falta, se reutiliza `AZURE_OPENAI_API_KEY`)

### TTS (Audio Speech)
- `AZURE_TTS_ENDPOINT=https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>/audio/speech?api-version=<ver>`
- `AZURE_TTS_MODEL=gpt-4o-mini-tts`
- `AZURE_TTS_API_KEY=<clave>` (si falta, se reutiliza `AZURE_OPENAI_API_KEY`)
- `TTS_VOICE=alloy`

### Observabilidad (opcional)
- `APPLICATIONINSIGHTS_CONNECTIONSTRING=InstrumentationKey=...;IngestionEndpoint=...;...`
  - Si está presente y el paquete está instalado, se configura Azure Monitor automáticamente.

## Ejecutar localmente
1) Crea `.env` con tus valores.
2) Instala dependencias y arranca el servidor:

```powershell
python -m pip install -r requirements.txt
python .\main.py
```

Swagger/OpenAPI:
- http://localhost:8000/docs
- http://localhost:8000/redoc

## API
### GET `/health`
Respuesta mínima para sondeo de estado:
```json
{"status": "ok"}
```

### POST `/v1/voice`
Multipart form-data:
- `file` (audio `.wav` o `.mp3`)

Ejemplo (PowerShell):
```powershell
curl -X POST "http://localhost:8000/v1/voice" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@C:\ruta\a\tu\audio.mp3;type=audio/mpeg"
```

Respuesta (200):
```json
{
  "transcription": "...",
  "response_text": "...",
  "audio_mime_type": "audio/mpeg",
  "audio_b64": "..."
}
```

Errores (ejemplos):
- 400: `{"detail":"Formato de audio no soportado"}`
- 422: `{"detail":"Solicitud inválida: datos no válidos"}`
- 502: `{"detail":"Error procesando audio o generando respuesta"}`

Todas las respuestas incluyen la cabecera `x-request-id` para correlación en logs y Application Insights.

> Nota: El endpoint devuelve audio en base64 por compatibilidad. Si prefieres streaming binario directo, se puede añadir como opción.

## Pruebas
Ejecuta la suite de tests con Python del entorno virtual:
```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Docker
Construcción y ejecución local:
```powershell
docker build -t voice-agent .
docker run -p 8000:8000 --env-file .env voice-agent
```

## CI/CD (Azure Web App – contenedor)
Workflow: `.github/workflows/main_savanttest.yml`
- Buildx, login a ACR, `docker build-push`, y despliegue a Azure Web App (container) con `azure/webapps-deploy@v2`.
- Requiere secretos configurados en el repositorio (credenciales de ACR y publish profile del Web App).

## Solución de problemas
- El servidor no arranca:
  - Verifica que instalaste `requirements.txt` en el venv y que `.env` tiene claves y endpoints válidos.
  - `python-multipart` es necesario para subir archivos.
- ASR falla:
  - Confirma `AZURE_AUDIO_TRANSCRIBE_*` (endpoint/model/key) y la `api-version` compatible.
- LLM falla (401/403):
  - Revisa `AZURE_OPENAI_*`, el deployment y permisos.
- TTS falla:
  - Confirma `AZURE_TTS_*` y la voz configurada. El servicio devuelve audio binario en `resp.content`.
- Application Insights no recibe datos:
  - Asegúrate de definir `APPLICATIONINSIGHTS_CONNECTIONSTRING` en el entorno del servicio (Azure App Service → Configuration).

## Roadmap
- Opción de respuesta binaria (streaming) para audio.
- Detección de idioma y selección automática de voz.
- Persistencia/URL para audio generado en lugar de base64.
- Métricas y trazas adicionales (OpenTelemetry) y dashboards en App Insights.
