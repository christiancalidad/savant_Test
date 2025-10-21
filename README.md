Voice Agent (ASR → LLM → TTS)

Servicio FastAPI que recibe audio (.wav/.mp3), lo transcribe (ASR directo a Azure), analiza el texto con un LLM (LangChain + Azure OpenAI) y devuelve audio sintetizado (TTS con Azure), junto con un JSON con la transcripción y la respuesta textual.

Características
- ASR: consumo directo del endpoint de Azure OpenAI Audio Transcriptions (multipart: model + file).
- NLP: LangChain con `AzureChatOpenAI` (deployment configurable).
- TTS: consumo directo del endpoint de Azure OpenAI Audio Speech (JSON body: model, input, voice).
- FastAPI con OpenAPI/Swagger.
- Dockerfile para contenedorización.
- CI básico con GitHub Actions (instala deps, corre tests, valida build Docker).
- Plantillas de despliegue: Render, Railway, Fly.io.

Estructura
- app/
	- app.py — FastAPI app, CORS y health
	- config.py — Variables de entorno (pydantic-settings) y derivaciones útiles
	- routers/voice.py — Endpoint POST /v1/voice
	- services/
		- asr.py — Llama a Azure Audio Transcriptions (REST)
		- nlp.py — LLM con LangChain + AzureChatOpenAI
		- tts.py — Llama a Azure Audio Speech (REST)
- tests/ — Pruebas (health y flujo de voz con stub)
- .github/workflows/ci.yml — Pipeline CI
- Dockerfile, .dockerignore — Contenedor listo
- render.yaml, railway.json, fly.toml — Despliegue

Requisitos
- Python 3.11+
- Variables de entorno en `.env` (ver sección siguiente)

Variables de entorno
Config mínimas para cada componente (no subas `.env` al repo):

- General LLM (LangChain + Azure OpenAI)
	- AZURE_OPENAI_API_KEY
	- AZURE_INFERENCE_ENDPOINT — opcional; si está presente, se deriva `AZURE_OPENAI_ENDPOINT` y `AZURE_OPENAI_DEPLOYMENT` automáticamente.
	- AZURE_OPENAI_ENDPOINT — opcional (si no usas `AZURE_INFERENCE_ENDPOINT`)
	- AZURE_OPENAI_DEPLOYMENT — opcional (si no usas `AZURE_INFERENCE_ENDPOINT`)
	- LLM_MODEL — opcional; si no hay deployment, se usa como tal
	- LLM_TEMPERATURE — por defecto 0.3
	- LLM_MAX_TOKENS — por defecto 1024

- ASR (Azure Audio Transcriptions)
	- AZURE_AUDIO_TRANSCRIBE_ENDPOINT (ej.: https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>/audio/transcriptions?api-version=2025-03-01-preview)
	- AZURE_AUDIO_TRANSCRIBE_MODEL (ej.: gpt-4o-mini-transcribe) — si falta, se infiere del endpoint
	- AZURE_AUDIO_API_KEY — si falta, se reutiliza `AZURE_OPENAI_API_KEY`

- TTS (Azure Audio Speech)
	- AZURE_TTS_ENDPOINT (ej.: https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>/audio/speech?api-version=2025-03-01-preview)
	- AZURE_TTS_MODEL (ej.: gpt-4o-mini-tts) — si falta, se infiere del endpoint
	- AZURE_TTS_API_KEY — si falta, se reutiliza `AZURE_OPENAI_API_KEY`
	- TTS_VOICE (ej.: alloy)

- Observabilidad (opcional)
	- AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true|false
	- APPLICATION_INSIGHTS_CONNECTION_STRING=<connection-string>

Instalación y ejecución local
1) Crear `.env` con tus valores.
2) Instalar dependencias y ejecutar el servidor:

```powershell
python -m pip install -r requirements.txt
python .\main.py
```

3) OpenAPI/Swagger:
- http://localhost:8000/docs
- http://localhost:8000/redoc

Uso del endpoint
- POST /v1/voice (multipart/form-data)
	- file: archivo de audio (.wav o .mp3)

Ejemplo con PowerShell (cambia la ruta del archivo):
```powershell
curl -X POST "http://localhost:8000/v1/voice" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@C:\Users\chris\OneDrive\Escritorio\GenAI\savant_test\savant_Test\test_recordings\test1.mp3;type=audio/mpeg"
```

Respuesta (JSON):
```json
{
	"transcription": "...",
	"response_text": "...",
	"audio_mime_type": "audio/mpeg",
	"audio_b64": "..."
}
```

Nota sobre audio binario
- Actualmente el endpoint devuelve JSON con `audio_b64` para máxima compatibilidad (Swagger, clientes HTTP). Si prefieres respuesta binaria (streaming) podemos añadir un flag de query (por ejemplo `?as_binary=true`) o un endpoint alterno. Dímelo y lo activo.

Tests
- Ejecuta pruebas con:
```powershell
pytest -q
```

Docker
- Construir y ejecutar:
```powershell
docker build -t voice-agent .
docker run -p 8000:8000 --env-file .env voice-agent
```

CI/CD
- GitHub Actions: `.github/workflows/ci.yml` instala dependencias, corre tests y construye imagen Docker.

Despliegue
- Render: `render.yaml`
- Railway: `railway.json`
- Fly.io: `fly.toml`

Solución de problemas
- El servidor no arranca:
	- Verifica que `requirements.txt` esté instalado en tu venv y que `.env` contenga claves y endpoints válidos.
	- Asegúrate de tener `python-multipart` instalado (incluido en requirements) para subir archivos.
- La transcripción es vacía o error:
	- Revisa `AZURE_AUDIO_TRANSCRIBE_ENDPOINT`, `AZURE_AUDIO_TRANSCRIBE_MODEL` y `AZURE_AUDIO_API_KEY`.
	- Valida que el deployment soporta transcripción de audio y la `api-version` sea correcta.
- El TTS falla o devuelve silencio:
	- Revisa `AZURE_TTS_ENDPOINT`, `AZURE_TTS_MODEL`, `AZURE_TTS_API_KEY` y `TTS_VOICE`.
	- El servicio devuelve audio binario; si cambia a JSON con campos de audio, hay que ajustar el parser.

Roadmap corto
- Opción de respuesta binaria nativa del endpoint (streaming) y descarga con extensión.
- Detección de idioma ASR y selección automática de voz TTS.
- Persistencia opcional del audio generado (URL en lugar de base64).
- Integración de OpenTelemetry (trazas/metricas) con Application Insights.
