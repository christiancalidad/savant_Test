import base64
from typing import Optional
import httpx

from app.config import settings


async def synthesize_speech(text: str, language: str = "es-ES") -> tuple[str, str]:
    """
    Llama al endpoint de Azure TTS (audio/speech) y retorna (mime_type, audio_base64).
    Si faltan variables, retorna un WAV de silencio para no romper el flujo.
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
        # La API de TTS puede devolver audio binario o un JSON con data.
        # Según el ejemplo, asumimos audio binario directo.
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

