import base64
import httpx

from app.config import settings


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

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        audio_bytes = resp.content
        mime = resp.headers.get("Content-Type", "audio/mpeg")
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return (mime, b64)
    except Exception:
        # Fallback ante error: 1s de silencio WAV
        silent_wav_bytes = _generate_silence_wav(seconds=1, sample_rate=8000)
        b64 = base64.b64encode(silent_wav_bytes).decode("utf-8")
        return ("audio/wav", b64)


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

