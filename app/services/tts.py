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
        - On any error (e.g., non-2xx status, network/timeout issues), returns a 1-second silent WAV
          (8000 Hz) encoded as Base64 with MIME type "audio/wav".
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

    if not endpoint or not api_key:
        raise RuntimeError("Azure TTS endpoint or API key not configured")

    # Azure OpenAI Audio Speech expects API key in 'api-key' header and an Accept for desired audio format
    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
        "api-key": api_key,
    }
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        # Some Azure deployments also accept an explicit output format hint
        "format": "mp3",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as http_err:
            # Log server's error body to aid debugging (e.g., invalid voice, bad api-version)
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
        mime = resp.headers.get("Content-Type", "audio/mpeg")
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return (mime, b64)
    except Exception as exc:
        logger.exception(f"TTS synthesis failed: {exc}")
        # Fallback: return 1-second silence to keep pipeline resilient
        try:
            silence = _generate_silence_wav(1)
            return ("audio/wav", base64.b64encode(silence).decode("utf-8"))
        except Exception:
            # If even silence generation fails, re-raise original error
            raise RuntimeError("TTS synthesis failed") from exc


def _generate_silence_wav(seconds: int, sample_rate: int = 8000) -> bytes:
    import io
    import wave
    import struct

    n_frames = seconds * sample_rate
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        silence_frame = struct.pack('<h', 0)
        for _ in range(n_frames):
            wf.writeframesraw(silence_frame)
    return buffer.getvalue()

