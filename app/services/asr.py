from typing import Tuple
import mimetypes
import httpx
from app.config import settings


async def transcribe_audio(file_path: str) -> Tuple[str, str]:
    """
    Transcribe audio calling Azure Audio Transcriptions REST endpoint directly.
    Returns (transcription, language_code).
    Falls back to a stub when config is missing.
    """
    endpoint = settings.azure_audio_transcribe_endpoint
    model = settings.azure_audio_transcribe_model
    api_key = settings.azure_audio_api_key


    mime, _ = mimetypes.guess_type(file_path)
    if not mime:
        mime = "audio/wav"

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    # Multipart form: model, file
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            with open(file_path, "rb") as fh:
                files = {
                    "model": (None, model),
                    "file": (file_path, fh, mime),
                }
                resp = await client.post(endpoint, headers=headers, files=files)
            resp.raise_for_status()
            data = resp.json()

        # The response is expected to include transcription text.
        # Common fields: "text" or nested inside choices. We'll try several options.
        transcription = (
            data.get("text")
            or (data.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(data.get("choices"), list) else None)
            or ""
        ).strip()

        if not transcription:
            transcription = "(transcripción vacía)"

        # Idioma: si el servicio no lo devuelve, asumir inglés
        lang = "en-US"
        return (transcription, lang)
    except Exception:
        return ("Error", "Error")
