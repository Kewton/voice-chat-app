# app/api/v1/endpoints/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import speech_recognition as sr
import json
import asyncio
import logging
from typing import Dict

from app.services.chat_service import ChatService, chat_service # Import instance
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accepts a new connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client connected: {client_id}, Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Removes a connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client disconnected: {client_id}, Total connections: {len(self.active_connections)}")

    async def send_text_message(self, message: str, client_id: str):
        """Sends a text message to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
                logger.debug(f"Sent text to {client_id}: {message}")
            except Exception as e:
                logger.error(f"Error sending text to {client_id}: {e}")
                # Consider disconnecting the client if send fails repeatedly
                # self.disconnect(client_id)

    async def send_audio_message(self, audio_bytes: bytes, client_id: str):
        """Sends audio data (bytes) to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_bytes(audio_bytes)
                logger.info(f"Sent {len(audio_bytes)} bytes of audio data to {client_id}")
            except Exception as e:
                logger.error(f"Error sending audio bytes to {client_id}: {e}")
                # Consider disconnecting the client


manager = ConnectionManager()


async def handle_audio_processing(client_id: str, service: ChatService):
    """Handles the audio recording, processing, and response loop."""
    try:
        with sr.Microphone(
            sample_rate=16000, # Consider making configurable if needed
            # device_index= Optional device index
        ) as source:
            # Optional: Adjust for ambient noise once upon connection/start
            # service.recognizer.adjust_for_ambient_noise(source)
            # logger.info(f"Adjusted for ambient noise for {client_id}")

            # Listen for audio
            audio_data = await service.recognize_speech(source)

            if audio_data:
                # Process audio to text (includes debug saving)
                recognized_text = await service.process_audio_to_text(audio_data, client_id)

                if recognized_text:
                    # Get LLM response
                    llm_response = await service.get_llm_response(recognized_text, client_id)
                    # Synthesize speech from LLM response
                    audio_response = await service.synthesize_speech(llm_response)
                    # Send synthesized audio back to client
                    await manager.send_audio_message(audio_response, client_id)
                else:
                    # Could not understand audio
                    await manager.send_text_message("ごめんなさい、よく聞き取れませんでした。", client_id)
            else:
                # Timeout occurred during listening
                await manager.send_text_message("...", client_id) # Indicate listening timeout

    except sr.RequestError as e:
        logger.error(f"Speech Recognition RequestError for {client_id}: {e}")
        await manager.send_text_message("音声認識サービスでエラーが発生しました。", client_id)
    except Exception as e:
        logger.error(f"Unexpected error during audio processing for {client_id}: {e}", exc_info=True)
        await manager.send_text_message("処理中にエラーが発生しました。", client_id)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    service: ChatService = Depends(lambda: chat_service) # Inject service instance
):
    """WebSocket endpoint for voice chat."""
    await manager.connect(websocket, client_id)
    service.initialize_conversation(client_id) # Initialize history on connect

    try:
        while True:
            # We expect text messages to trigger actions, like 'start_recording'
            data = await websocket.receive()

            if data["type"] == "websocket.receive":
                if "text" in data:
                    try:
                        message = json.loads(data["text"])
                        if message.get("type") == "start_recording":
                            logger.info(f"Received 'start_recording' from {client_id}")
                            # Run audio processing in the background
                            asyncio.create_task(handle_audio_processing(client_id, service))
                        else:
                            logger.warning(f"Received unknown text message type from {client_id}: {message}")
                            await manager.send_text_message("不明なコマンドです。", client_id)
                    except json.JSONDecodeError:
                        logger.error(f"Received invalid JSON from {client_id}: {data['text']}")
                        await manager.send_text_message("無効なメッセージ形式です。", client_id)
                    except Exception as e:
                        logger.error(f"Error processing message from {client_id}: {e}", exc_info=True)
                        await manager.send_text_message("メッセージ処理中にエラーが発生しました。", client_id)

                elif "bytes" in data:
                    # Handle binary data if needed in the future
                    # logger.info(f"Received {len(data['bytes'])} bytes from {client_id}. Discarding.")
                    pass # Currently not expecting binary data from client

            elif data["type"] == "websocket.disconnect":
                logger.info(f"Received disconnect event for {client_id}")
                raise WebSocketDisconnect(code=data.get("code", 1000)) # Propagate disconnect

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client: {client_id}")
    except Exception as e:
        # Catch potential unexpected errors during receive loop
        logger.error(f"Unexpected error in WebSocket loop for {client_id}: {e}", exc_info=True)
        # Try to send an error message if connection is still active
        if client_id in manager.active_connections:
            await manager.send_text_message("サーバー内部で予期せぬエラーが発生しました。", client_id)
    finally:
        manager.disconnect(client_id)
        service.clear_conversation(client_id) # Clean up history on disconnect
        logger.info(f"Cleaned up resources for client: {client_id}")
