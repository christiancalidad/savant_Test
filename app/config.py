from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import urlparse

class Settings(BaseSettings):
    app_name: str = "voice-agent"
    environment: str = Field(default="development", description="Environment name")

    # Azure Inference (full URL) and OpenAI service
    azure_inference_endpoint: Optional[str] = Field(default=None, validation_alias="AZURE_INFERENCE_ENDPOINT")
    azure_openai_endpoint: Optional[str] = Field(default=None, validation_alias="AZURE_OPENAI_ENDPOINT")
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

    def model_post_init(self, __context: dict) -> None:  # pydantic v2 hook
        # Si sólo tenemos AZURE_INFERENCE_ENDPOINT, intentamos derivar base endpoint y deployment
        if self.azure_inference_endpoint and (not self.azure_openai_endpoint or not self.azure_openai_deployment):
            try:
                # Ejemplo: https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>/chat/completions?api-version=...
                u = urlparse(self.azure_inference_endpoint)
                self.azure_openai_endpoint = f"{u.scheme}://{u.netloc}"
                # Extraer deployment entre '/deployments/{name}/'
                parts = [p for p in u.path.split('/') if p]
                if "deployments" in parts:
                    idx = parts.index("deployments")
                    if idx + 1 < len(parts):
                        self.azure_openai_deployment = parts[idx + 1]
            except Exception:
                pass

        # If no specific audio API key is provided, reuse the OpenAI API key
        if not self.azure_audio_api_key and self.azure_openai_api_key:
            self.azure_audio_api_key = self.azure_openai_api_key

        # Derive audio transcribe model from endpoint if not set
        if self.azure_audio_transcribe_endpoint and not self.azure_audio_transcribe_model:
            try:
                u2 = urlparse(self.azure_audio_transcribe_endpoint)
                parts2 = [p for p in u2.path.split('/') if p]
                if "deployments" in parts2:
                    idx2 = parts2.index("deployments")
                    if idx2 + 1 < len(parts2):
                        self.azure_audio_transcribe_model = parts2[idx2 + 1]
            except Exception:
                pass

        # If LLM model is provided and no deployment set, use llm_model as deployment name
        if self.llm_model and not self.azure_openai_deployment:
            self.azure_openai_deployment = self.llm_model

        # Reuse OpenAI API key for TTS if specific missing
        if not self.azure_tts_api_key and self.azure_openai_api_key:
            self.azure_tts_api_key = self.azure_openai_api_key

        # Derive TTS model from endpoint if not provided
        if self.azure_tts_endpoint and not self.azure_tts_model:
            try:
                u3 = urlparse(self.azure_tts_endpoint)
                parts3 = [p for p in u3.path.split('/') if p]
                if "deployments" in parts3:
                    idx3 = parts3.index("deployments")
                    if idx3 + 1 < len(parts3):
                        self.azure_tts_model = parts3[idx3 + 1]
            except Exception:
                pass

settings = Settings()