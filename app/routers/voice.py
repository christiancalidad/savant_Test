from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.schemas import VoiceResponse
from app.services.asr import transcribe_audio
from app.services.nlp import generate_response
from app.services.tts import synthesize_speech
import tempfile
import shutil

router = APIRouter(prefix="/v1", tags=["voice"])

@router.post("/voice", response_model=VoiceResponse)
async def voice_pipeline(file: UploadFile = File(...)):
    if file.content_type not in {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3"}:
        raise HTTPException(status_code=400, detail="Formato de audio no soportado")

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    # ASR
    transcription, language = await transcribe_audio(tmp_path)

    print(f"Transcription: {transcription} (lang: {language})")

    # NLP
    response_text = await generate_response(transcription, language)

    print(f"Response Text: {response_text}")

    # TTS
    audio_mime, audio_b64 = await synthesize_speech(response_text, language)

    return JSONResponse(
        content=VoiceResponse(
            transcription=transcription,
            response_text=response_text,
            audio_mime_type=audio_mime,
            audio_b64=audio_b64,
        ).model_dump()
    )
