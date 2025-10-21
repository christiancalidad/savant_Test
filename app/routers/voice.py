import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from app.schemas import VoiceResponse
from app.services.asr import transcribe_audio
from app.services.nlp import generate_response
from app.services.tts import synthesize_speech
import tempfile
import shutil

router = APIRouter(prefix="/v1", tags=["voice"])
logger = logging.getLogger("app.voice")

@router.post("/voice", response_model=VoiceResponse)

async def voice_pipeline(request: Request, file: UploadFile = File(...)):
    """
Process an uploaded audio file through ASR, NLP, and TTS, returning the transcript, generated reply, and synthesized audio.
    This FastAPI endpoint:
    - Validates that the uploaded file's MIME type is one of: "audio/wav", "audio/x-wav", "audio/mpeg", or "audio/mp3".
    - Saves the upload to a temporary file on disk.
    - Runs automatic speech recognition via `transcribe_audio` to obtain the transcription and detected language.
    - Generates a textual response via `generate_response` based on the transcription.
    - Synthesizes speech via `synthesize_speech`, producing an audio MIME type and a base64-encoded audio payload.
    - Returns a JSONResponse matching the `VoiceResponse` schema.
    Args:
        file (UploadFile): The uploaded audio file to process.
    Returns:
        JSONResponse: A JSON payload conforming to `VoiceResponse` with:
            - transcription (str): Recognized text from the input audio.
            - response_text (str): The generated textual response.
            - audio_mime_type (str): MIME type of the synthesized audio.
            - audio_b64 (str): Base64-encoded synthesized audio.
    Raises:
        HTTPException: 400 if the uploaded content type is not supported.
    Notes:
        - A temporary file is created for processing and is not deleted within this function.
        - Intended to be used as a FastAPI POST route handler at "/voice".
    """
    request_id = getattr(request.state, "request_id", "-")
    if file.content_type not in {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/webm", "audio/ogg"}:
        logger.warning(f"Unsupported content type: {file.content_type} | request_id={request_id}")
        raise HTTPException(status_code=400, detail="Formato de audio no soportado")

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name 

    try:
        logger.info(f"Starting ASR | tmp_path={tmp_path} | request_id={request_id}")
        transcription, language = await transcribe_audio(tmp_path)
        logger.info(f"ASR done | lang={language} | request_id={request_id}")

        logger.info(f"Starting NLP | request_id={request_id}")
        response_text = await generate_response(transcription)
        logger.info(f"NLP done | chars={len(response_text)} | request_id={request_id}")

        logger.info(f"Starting TTS | request_id={request_id}")
        audio_mime, audio_b64 = await synthesize_speech(response_text)
        logger.info(f"TTS done | mime={audio_mime} | bytes={len(audio_b64) if audio_b64 else 0} | request_id={request_id}")
    except HTTPException:
        # Bubble up HTTPExceptions as-is
        raise
    except Exception as exc:
        logger.exception(f"Voice pipeline failed: {exc} | request_id={request_id}")
        raise HTTPException(status_code=502, detail="Error procesando audio o generando respuesta")

    return JSONResponse(
        content=VoiceResponse(
            transcription=transcription,
            response_text=response_text,
            audio_mime_type=audio_mime,
            audio_b64=audio_b64,
        ).model_dump()
    )
