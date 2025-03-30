# app/services/chat_service.py
import speech_recognition as sr
import google.generativeai as genai
from openai import AsyncOpenAI
import pyaudio
import logging
import time
import asyncio
from typing import Dict, List, Tuple
from pathlib import Path
import datetime

from app.core.config import settings, SAFETY_SETTINGS, GENERATION_CONFIG
from app.utils.file_utils import ensure_directory_exists

logger = logging.getLogger(__name__)


class ChatService:
    """Handles speech recognition, LLM interaction, and TTS."""

    def __init__(self):
        """Initializes API clients and recognizer."""
        # Configure Gemini
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.gemini_model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS,
        )
        logger.info(f"Gemini model '{settings.GEMINI_MODEL_NAME}' initialized.")

        # Configure OpenAI
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found in environment variables.")
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info(f"OpenAI client initialized for TTS model '{settings.TTS_MODEL_NAME}'.")

        # Configure Speech Recognition
        self.recognizer = sr.Recognizer()
        logger.info("Speech Recognizer initialized.")

        # Configure PyAudio (for TTS, only need settings here)
        self._pyaudio_instance = pyaudio.PyAudio()
        logger.info("PyAudio instance created.")

        # In-memory conversation history store
        self.conversations: Dict[str, List[Dict]] = {}

    def initialize_conversation(self, client_id: str):
        """
        Initializes or resets the conversation history for a client.

        Args:
            client_id: The unique identifier for the client.
        """
        self.conversations[client_id] = []
        logger.info(f"Initialized conversation history for client: {client_id}")

    def clear_conversation(self, client_id: str):
        """
        Clears the conversation history for a client.

        Args:
            client_id: The unique identifier for the client.
        """
        if client_id in self.conversations:
            del self.conversations[client_id]
            logger.info(f"Cleared conversation history for client: {client_id}")

    def _save_debug_audio(self, audio_data: sr.AudioData, client_id: str) -> None:
        """
        Saves the audio data as a WAV file if debug mode is enabled.

        Args:
            audio_data: The recognized audio data.
            client_id: The client identifier.
        """
        if settings.DEBUG_MODE:
            try:
                ensure_directory_exists(settings.AUDIO_SAVE_PATH)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = settings.AUDIO_SAVE_PATH / f"audio_{client_id}_{timestamp}.wav"
                with open(filename, "wb") as f:
                    f.write(audio_data.get_wav_data())
                logger.info(f"Debug audio saved to: {filename}")
            except Exception as e:
                logger.error(f"Failed to save debug audio for client {client_id}: {e}")

    async def recognize_speech(self, source: sr.AudioSource) -> sr.AudioData | None:
        """
        Listens to the audio source and recognizes speech.

        Args:
            source: The audio source (e.g., sr.Microphone()).

        Returns:
            The recognized AudioData object, or None if timeout occurs.

        Raises:
            sr.RequestError: If there's an issue with the speech recognition service.
        """
        logger.info(f"Listening for audio... (Timeout: {settings.SR_TIMEOUT}s, Limit: {settings.SR_PHRASE_TIME_LIMIT}s)")
        try:
            audio = self.recognizer.listen(
                source,
                timeout=settings.SR_TIMEOUT,
                phrase_time_limit=settings.SR_PHRASE_TIME_LIMIT
            )
            logger.info("Audio received.")
            return audio
        except sr.WaitTimeoutError:
            logger.warning("Listening timed out, no speech detected.")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from speech recognition service; {e}")
            raise

    async def process_audio_to_text(
        self,
        audio_data: sr.AudioData,
        client_id: str
    ) -> str | None:
        """
        Processes audio data to text using Speech Recognition and handles debug saving.

        Args:
            audio_data: The audio data to process.
            client_id: The client identifier.

        Returns:
            The recognized text, or None if recognition fails.

        Raises:
            sr.RequestError: Forwarded from recognize_google.
        """
        try:
            # Save audio if in debug mode BEFORE attempting recognition
            self._save_debug_audio(audio_data, client_id)

            text = self.recognizer.recognize_google(audio_data, language=settings.SR_LANGUAGE)
            logger.info(f"Recognized text for {client_id}: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning(f"Speech Recognition could not understand audio for client {client_id}.")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service for client {client_id}; {e}")
            raise # Re-raise to be handled by the endpoint

    async def get_llm_response(self, text: str, client_id: str) -> str:
        """
        Gets a response from the configured LLM (Gemini).

        Args:
            text: The user's input text.
            client_id: The client identifier for managing conversation history.

        Returns:
            The LLM's response text.

        Raises:
            Exception: If the LLM API call fails.
        """
        if client_id not in self.conversations:
            self.initialize_conversation(client_id) # Ensure history exists

        # Prepend prompt instructions
        prompt = f"""
        あなたはてぃ先生です。保育士のプロです。
        質問に対し3~4歳児向けに回答し、150~200文字程度に要約し端的に回答してください。質問は次です。
        {text}
        """
        self.conversations[client_id].append({"role": "user", "parts": [prompt]})
        logger.debug(f"Conversation history for {client_id} before LLM call: {self.conversations[client_id]}")

        try:
            chat = self.gemini_model.start_chat(history=self.conversations[client_id][:-1]) # Exclude the last user message from history passed to start_chat
            response = await chat.send_message_async(prompt) # Send the actual prompt
            llm_response = response.text
            logger.info(f"LLM response for {client_id}: {llm_response}")

            # Add LLM response to history
            self.conversations[client_id].append({"role": "model", "parts": [llm_response]})
            return llm_response
        except Exception as e:
            logger.error(f"Error getting LLM response for {client_id}: {e}")
            # Remove the failed user prompt from history
            if self.conversations[client_id] and self.conversations[client_id][-1]["role"] == "user":
                self.conversations[client_id].pop()
            raise Exception("LLM API call failed.") from e

    async def synthesize_speech(self, text: str) -> bytes:
        """
        Synthesizes speech from text using OpenAI TTS API asynchronously.

        Args:
            text: The text to synthesize.

        Returns:
            The synthesized audio data in PCM format as bytes.

        Raises:
            Exception: If the TTS API call fails.
        """
        logger.info(f"Synthesizing speech for text: '{text[:50]}...'")
        start_time = time.time()
        accumulated_audio = bytearray()

        try:
            async with self.openai_client.audio.speech.with_streaming_response.create(
                model=settings.TTS_MODEL_NAME,
                voice=settings.TTS_VOICE,
                input=text,
                instructions=settings.TTS_INSTRUCTIONS,
                response_format=settings.TTS_RESPONSE_FORMAT,
            ) as response:
                first_byte_time = time.time()
                logger.info(f"Time to first byte (TTS): {int((first_byte_time - start_time) * 1000)}ms")
                async for chunk in response.iter_bytes(chunk_size=settings.TTS_CHUNK_SIZE):
                    accumulated_audio.extend(chunk)
            end_time = time.time()
            logger.info(f"TTS synthesis done in {int((end_time - start_time) * 1000)}ms. Size: {len(accumulated_audio)} bytes.")
            return bytes(accumulated_audio)
        except Exception as e:
            logger.error(f"Error during TTS synthesis: {e}")
            raise Exception("TTS API call failed.") from e


# Single instance of the service
chat_service = ChatService()
