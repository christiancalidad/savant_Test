from typing import Tuple
import logging
import mimetypes
import httpx
from app.config import settings

logger = logging.getLogger("app.asr")

async def transcribe_audio(file_path: str) -> Tuple[str, str]:
    """
    Transcribe an audio file asynchronously using an Azure-compatible transcription endpoint.
    This function uploads the audio as multipart/form-data with the provided model and
    extracts the transcription from common response shapes.
    Parameters:
    - file_path: Path to the local audio file to transcribe. The MIME type is inferred via
        mimetypes.guess_type and defaults to "audio/wav" when unknown.
    Returns:
    - (text, lang): A tuple where:
        - text: The transcribed text. If the API returns no text, the placeholder
            "(transcripción vacía)" is used. On error, "Error".
        - lang: BCP-47 language tag of the transcription. Currently always "en-US".
            On error, "Error".
    Behavior:
    - Sends a POST request to the configured endpoint with Authorization: Bearer <api_key>.
    - Multipart form fields: "model" (string) and "file" (the audio content).
    - Parses JSON response, preferring "text", then falling back to choices[0].message.content.
    - Trims surrounding whitespace from the resulting transcription.
    Error handling:
    - Any exception (file I/O, network issues, non-2xx status, JSON parsing) results in
        a return value of ("Error", "Error") instead of raising.
    Notes:
    - Uses httpx.AsyncClient with a 60-second timeout.
    - Requires configured settings:
        - settings.azure_audio_transcribe_endpoint
        - settings.azure_audio_transcribe_model
        - settings.azure_audio_api_key
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

        transcription = (
            data.get("text")
            or (data.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(data.get("choices"), list) else None)
            or ""
        ).strip()

        if not transcription:
            transcription = "(transcripción vacía)"

        lang = "en-US"
        return (transcription, lang)
    except Exception as exc:
        logger.exception(f"ASR transcription failed: {exc}")
        raise RuntimeError("ASR transcription failed") from exc
