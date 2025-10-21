import base64
import logging
import httpx

from app.config import settings

logger = logging.getLogger("app.tts")

async def synthesize_speech(text: str) -> tuple[str, str]:
    """
    Asynchronously synthesize speech audio from text using a configured Azure-compatible TTS API.
    Args:
        text: The text to convert to speech.
    Returns:
        A tuple (mime_type, audio_base64):
        - mime_type: The audio MIME type reported by the service (defaults to "audio/mpeg").
        - audio_base64: The audio content encoded in Base64.
    Behavior:
        - Sends a JSON POST request to the configured TTS endpoint with the model and voice.
        - On HTTP success, returns the service's audio bytes as Base64 along with the response Content-Type.
        - On any error (e.g., non-2xx status, network/timeout issues), raises a RuntimeError so the caller can surface the error.
    Notes:
        - Uses a 60-second HTTP client timeout.
        - Voice is taken from settings (fallback "alloy"). Model, endpoint, and API key are also read from settings.
    Example:
        mime, audio_b64 = await synthesize_speech("Hello world")
    """

    endpoint = settings.azure_tts_endpoint
    model = settings.azure_tts_model
    api_key = settings.azure_tts_api_key
    voice = settings.tts_voice or "alloy"

    # Azure OpenAI Audio Speech expects API key in 'api-key' header and an Accept for desired audio format
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "input": text,
        "voice": voice
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            print(endpoint, headers, payload)
            resp = await client.post(endpoint, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as http_err:
            # Log server's error body to aid debugging (e.g., invalid voice, bad api-version)
            print(http_err)
            body_text = http_err.response.text if http_err.response is not None else "<no body>"
            logger.error(
                "TTS HTTP %s: %s | url=%s | body=%s",
                http_err.response.status_code if http_err.response else "?",
                str(http_err),
                getattr(http_err.request, 'url', endpoint),
                body_text[:2000],
            )
            raise
        
        audio_bytes = resp.content
        logger.info("TTS synthesis succeeded", extra={"bytes": len(audio_bytes)})
        mime = resp.headers.get("Content-Type", "audio/mpeg")
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return (mime, b64)
    except Exception as exc:
        logger.exception(f"TTS synthesis failed: {exc}")
        # Do not generate silence; surface the error to the caller
        raise RuntimeError("TTS synthesis failed") from exc

