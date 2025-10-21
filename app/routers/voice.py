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
    response_text = await generate_response(transcription)

    print(f"Response Text: {response_text}")

    # TTS
    audio_mime, audio_b64 = await synthesize_speech(response_text)

    return JSONResponse(
        content=VoiceResponse(
            transcription=transcription,
            response_text=response_text,
            audio_mime_type=audio_mime,
            audio_b64=audio_b64,
        ).model_dump()
    )
