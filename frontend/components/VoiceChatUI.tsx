"use client";

import { useEffect, useState, useRef } from 'react';
import io, { Socket } from 'socket.io-client';
import animationData from '../public/animation.json';
import Lottie from 'react-lottie';

export default function VoiceChatUI() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const lottieRef = useRef<any>(null);
  const [, setSocket] = useState<Socket | null>(null);
  const [fastAPIWebSocket, setFastAPIWebSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    // NestJS WebSocket サーバーへの接続 (確認用)
    const socket = io('http://127.0.0.1:3001/voice-chat');
    setSocket(socket);

    // FastAPI WebSocket サーバーへの接続
    const clientId = generateClientId();
    const fastAPIWs = new WebSocket(`ws://127.0.0.1:5000/ws/${clientId}`);
    setFastAPIWebSocket(fastAPIWs);

    fastAPIWs.onopen = () => {
      console.log('FastAPI WebSocket connection opened:', clientId);
    };

    fastAPIWs.onmessage = (event) => {
      console.log('Message from FastAPI server:', event.data);
      speak(event.data);
    };

    fastAPIWs.onerror = (error) => {
      console.error('FastAPI WebSocket error:', error);
    };

    return () => {
      socket.disconnect();
      fastAPIWs.close();
    };
  }, []); // 依存配列を空にする

  const generateClientId = () => {
    return "client_" + Math.random().toString(36).substring(2, 15);
  };

  const speak = (text: string) => {
    setIsPlaying(true);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ja-JP';
    utterance.onend = () => setIsPlaying(false);
    utterance.onstart = () => setIsPlaying(true);
    speechSynthesis.speak(utterance);
  };

  const handleMicPress = () => {
    setIsRecording(true);
    // FastAPI サーバーに録音開始を通知
    if (fastAPIWebSocket && fastAPIWebSocket.readyState === WebSocket.OPEN) {
      fastAPIWebSocket.send(JSON.stringify({ type: "start_recording" }));
    }
  };

  const handleMicRelease = () => {
    setIsRecording(false);
    // FastAPI サーバーに録音停止を通知（必要に応じて実装）
  };

  const defaultOptions = {
    loop: true,
    autoplay: false,
    animationData: animationData,
    rendererSettings: {
      preserveAspectRatio: 'xMidYMid slice'
    }
  };

  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ width: '200px', height: '200px', margin: '0 auto' }}>
        <Lottie
          options={defaultOptions}
          height={200}
          width={200}
          isStopped={!isPlaying}
          isPaused={!isPlaying}
          ref={lottieRef}
        />
      </div>
      <button
        style={{
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          backgroundColor: isRecording ? 'red' : 'blue',
          border: 'none',
          marginTop: '20px',
          fontSize: '50px',
        }}
        onMouseDown={handleMicPress}
        onMouseUp={handleMicRelease}
        onTouchStart={handleMicPress}
        onTouchEnd={handleMicRelease}
      >
        🎤
      </button>
      {isRecording && <p>おはなしちゅう…</p>}
      {isPlaying && <p>おへんじちゅう…</p>}
    </div>
  );
}