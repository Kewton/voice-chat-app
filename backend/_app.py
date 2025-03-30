# backend/app.py (FastAPI)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr
import google.generativeai as genai  # Google Gemini
import json
import os
from typing import Dict, List
from dotenv import load_dotenv
import asyncio
from openai import AsyncOpenAI
import time
import pyaudio


load_dotenv(verbose=True)

# LLM APIキーの設定 (環境変数から)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
# Geminiモデルの設定
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# SpeechRecognition の初期化
r = sr.Recognizer()


async def synthesize_speech(
    text: str,
    voice: str = "coral",
    instructions: str = "Speak in a cheerful and positive tone."
) -> bytes:
    """
    OpenAIのTTS APIを用い、テキストからPCM形式の音声データを非同期に生成します。
    """
    player_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

    start_time = time.time()

    print(f"tts test:{text}")
    async with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        instructions=instructions,
        response_format="pcm",
    ) as response:
        print(f"Time to first byte: {int((time.time() - start_time) * 1000)}ms")
        async for chunk in response.iter_bytes(chunk_size=1024):
            # print(chunk)
            player_stream.write(chunk)
    print(f"Done in {int((time.time() - start_time) * 1000)}ms.")
    return bytes(player_stream)


# FastAPI インスタンスの作成
app = FastAPI()

# CORS 設定 (開発中は "*" でOK。本番環境では適切なオリジンを設定)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会話履歴を保存する辞書型
conversations: Dict[str, List[Dict]] = {}


# WebSocket接続を管理するクラス
class ConnectionManager:
    def __init__(self):
        # 修正
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        # 初期化
        conversations[client_id] = []

    def disconnect(self, client_id: str):
        del self.active_connections[client_id]
        if client_id in conversations:
            del conversations[client_id]

    async def send_text_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)


manager = ConnectionManager()


# 音声認識とLLM応答のための非同期関数
async def process_audio(audio_data: sr.AudioData, client_id: str):
    try:
        text = r.recognize_google(audio_data, language='ja-JP')
        print(f"Recognized: {text}")

        # 音声データをWAVファイルとして保存 (デバッグ用)
        with open(f"audio_{client_id}.wav", "wb") as f:
            f.write(audio_data.get_wav_data())
        print(f"Audio saved to audio_{client_id}.wav")

        # 会話履歴に追加
        if client_id in conversations:
            _text = """
            あなたはてぃ先生です。保育士のプロです。
            質問に対し3~4歳児向けに回答し、150~200文字程度に要約し端的に回答してください。質問は次です。
            """
            _text += text
            conversations[client_id].append({"role": "user", "parts": [_text]})
        print(conversations)
        # LLMで応答を生成 (ChatGPTの例)
        # response = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #          {"role": "system", "content": "あなたは子供向けの優しいアシスタントです。ひらがなで短く答えてください。"},
        #         *conversations[client_id] # 過去の会話履歴
        #     ]
        # )
        # llm_response = response.choices[0].message.content

        # gemini
        if client_id in conversations:
            chat = model.start_chat(history=conversations[client_id])
            llm_response = chat.send_message(text).text
            print(llm_response)

        # 応答を履歴に追加
        if client_id in conversations:
            conversations[client_id].append({"role": "model", "parts": [llm_response]})

        # 0329 コメントアウト
        # # クライアントに応答を送信
        # await manager.send_text_message(llm_response, client_id)
        # ##

        # TTS APIでテキストを音声に変換（PCM形式）
        audio_bytes = await synthesize_speech(llm_response)

        # クライアントへ音声データ（バイナリ）を送信
        await manager.send_audio_message(audio_bytes, client_id)

    except sr.UnknownValueError:
        await manager.send_text_message("ごめんなさい、よく聞き取れませんでした。", client_id)
    except sr.RequestError as e:
        await manager.send_text_message("エラーが発生しました。", client_id)
        print(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        print(e)
        if "cannot convert 'Stream' object to bytes" != str(e):
            await manager.send_text_message("エラーが発生しました。", client_id)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    print(f"Client connected: {client_id}")
    try:
        while True:
            data = await websocket.receive()
            # 切断メッセージの場合はループを抜ける
            if data["type"] == "websocket.disconnect":
                break

            print(data)
            # 通常の受信処理（テキストメッセージの場合）
            if data["type"] == "websocket.receive" and "text" in data:
                data_json = json.loads(data["text"])
                if data_json["type"] == "start_recording":
                    # 音声認識処理を非同期で実行
                    print("音声認識処理を非同期で実行")
                    with sr.Microphone() as source:
                        try:
                            # タイムアウトを設定
                            audio = r.listen(source, timeout=5, phrase_time_limit=8)
                            asyncio.create_task(process_audio(audio, client_id))
                        except sr.WaitTimeoutError:
                            # タイムアウトの時
                            await manager.send_text_message("...", client_id)
                        except Exception as e:
                            await manager.send_text_message("エラーが発生しました。", client_id)
                            print(e)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(client_id)
        print(f"Client disconnected: {client_id}")
