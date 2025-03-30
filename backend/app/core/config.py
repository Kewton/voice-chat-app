# app/core/config.py
import os
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# .env ファイルのパスを取得 (プロジェクトルートにあることを想定)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, verbose=True)


class Settings(BaseSettings):
    """Application settings."""

    # LLM API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Gemini Settings
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    GEMINI_TEMPERATURE: float = 0.9
    GEMINI_TOP_P: float = 1.0
    GEMINI_TOP_K: int = 1
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048

    # OpenAI TTS Settings
    TTS_MODEL_NAME: str = "gpt-4o-mini-tts"
    TTS_VOICE: str = "coral"
    TTS_INSTRUCTIONS: str = "Speak in a cheerful and positive tone."
    TTS_RESPONSE_FORMAT: str = "pcm"
    TTS_CHUNK_SIZE: int = 1024

    # Speech Recognition Settings
    SR_LANGUAGE: str = "ja-JP"
    SR_TIMEOUT: int = 5 # seconds
    SR_PHRASE_TIME_LIMIT: int = 8 # seconds

    # Debug Settings
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    AUDIO_SAVE_PATH: Path = Path(os.getenv("AUDIO_SAVE_PATH", "../tmp"))

    # CORS Settings (adjust for production)
    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # PyAudio Settings
    # pyaudio.paInt16
    PYAUDIO_FORMAT: int = 8
    PYAUDIO_CHANNELS: int = 1
    PYAUDIO_RATE: int = 24000

    class Config:
        """Pydantic BaseSettings config."""
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()

# Safety Settings for Gemini (example, adjust as needed)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Generation Config for Gemini
GENERATION_CONFIG = {
    "temperature": settings.GEMINI_TEMPERATURE,
    "top_p": settings.GEMINI_TOP_P,
    "top_k": settings.GEMINI_TOP_K,
    "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
}