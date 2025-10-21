from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import urlparse

class Settings(BaseSettings):
    app_name: str = "voice-agent"
    environment: str = Field(default="development", description="Environment name")

    # Azure Inference (full URL) and OpenAI service
    azure_openai_endpoint: Optional[str] = Field(default=None, validation_alias="AZURE_INFERENCE_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, validation_alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment: Optional[str] = Field(default=None, description="Azure OpenAI deployment name")
    azure_openai_api_version: str = Field(default="2025-01-01-preview")

    # LLM options
    llm_model: Optional[str] = Field(default=None, validation_alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, validation_alias="LLM_MAX_TOKENS")
    prompts_version: Optional[str] = Field(default=None, validation_alias="PROMPTS_VERSION")

    # Azure Speech (ASR/TTS) — opcional si se usa multimodal para ASR
    azure_speech_key: Optional[str] = None
    azure_speech_region: Optional[str] = None


    # Direct audio transcription endpoint (new)
    azure_audio_transcribe_endpoint: Optional[str] = Field(default=None, validation_alias="AZURE_AUDIO_TRANSCRIBE_ENDPOINT")
    azure_audio_transcribe_model: Optional[str] = Field(default=None, validation_alias="AZURE_AUDIO_TRANSCRIBE_MODEL")
    azure_audio_api_key: Optional[str] = Field(default=None, validation_alias="AZURE_AUDIO_API_KEY")

    # Azure TTS (audio/speech)
    azure_tts_endpoint: Optional[str] = Field(default=None, validation_alias="AZURE_TTS_ENDPOINT")
    azure_tts_model: Optional[str] = Field(default=None, validation_alias="AZURE_TTS_MODEL")
    azure_tts_api_key: Optional[str] = Field(default=None, validation_alias="AZURE_TTS_API_KEY")
    tts_voice: str = Field(default="alloy", validation_alias="TTS_VOICE")

    class Config:
        env_file = ".env"
        case_sensitive = False

    

settings = Settings()