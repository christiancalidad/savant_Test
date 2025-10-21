from pydantic import BaseModel
from typing import Optional

class VoiceResponse(BaseModel):
    transcription: str
    response_text: str
    audio_mime_type: str = "audio/wav"
    audio_b64: Optional[str] = None  # small demo responses inline; in prod return URL

class ErrorResponse(BaseModel):
    detail: str
