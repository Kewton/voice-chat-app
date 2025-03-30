"use client";

import { useEffect, useState, useRef } from 'react';
import io, { Socket } from 'socket.io-client';
import animationData from '../public/animation.json'; // public ディレクトリからのパスに変更
import Lottie from 'react-lottie';

// マイクの状態を表す型
type MicState = 'idle' | 'recording' | 'playing';

// 環境変数を取得 (クライアントサイドで利用可能)
const nestJsWsUrl = process.env.NEXT_PUBLIC_NESTJS_WS_URL || 'ws://127.0.0.1:3001/voice-chat'; // デフォルト値設定
const fastApiWsUrlBase = process.env.NEXT_PUBLIC_FASTAPI_WS_URL || 'ws://127.0.0.1:5000/ws/'; // デフォルト値設定

export default function VoiceChatUI() {
  const [micState, setMicState] = useState<MicState>('idle'); // 'idle', 'recording', 'playing'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const lottieRef = useRef<any>(null);
  const [, setSocket] = useState<Socket | null>(null); // NestJS Socket (現状維持)
  const [fastAPIWebSocket, setFastAPIWebSocket] = useState<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  useEffect(() => {
    // NestJS WebSocket サーバーへの接続 (確認用 - 変更なし)
    console.log("Using NestJS WS URL:", nestJsWsUrl);
    console.log("Using FastAPI WS Base URL:", fastApiWsUrlBase);
    // 環境変数のURLが `ws://host:port/namespace` 形式であることを想定
    // Socket.IOクライアントは http/https で接続を開始する
    const nestHttpUrl = nestJsWsUrl.replace(/^ws/, 'http');
    const nestSocket = io(nestHttpUrl); // URLに名前空間が含まれていると仮定
    setSocket(nestSocket);

    // FastAPI WebSocket サーバーへの接続
    const clientId = generateClientId();
    const fastApiWsUrl = `${fastApiWsUrlBase}${clientId}`;
    const ws = new WebSocket(fastApiWsUrl);
    setFastAPIWebSocket(ws);

    ws.onopen = () => {
      console.log('FastAPI WebSocket connection opened:', clientId);
    };

    ws.onmessage = (event) => {
      console.log('Message from FastAPI server:', event.data);
      // FastAPIからのメッセージ（テキスト）を受信したら読み上げ開始
      if (typeof event.data === 'string') {
          speak(event.data);
      } else if (event.data instanceof Blob) {
          // Blobデータ（音声など）を受信した場合の処理（必要なら）
          console.log("Received audio data from FastAPI");
          // ここでBlobデータを再生するなどの処理を追加できます
          // バイナリデータ（音声）が届いた場合
          setMicState('playing'); // 再生中状態にする
          const audioUrl = URL.createObjectURL(event.data);
          const audio = new Audio(audioUrl);
          audio.play();
          audio.onended = () => setMicState('idle'); // 再生完了でidleに戻す
          // 例: const audioUrl = URL.createObjectURL(event.data);
          //     const audio = new Audio(audioUrl);
          //     audio.play();
          //     setMicState('playing'); // 再生中状態にする
          //     audio.onended = () => setMicState('idle'); // 再生完了でidleに戻す
      }
    };

    ws.onerror = (error) => {
      console.error('FastAPI WebSocket error:', error);
      setMicState('idle'); // エラー発生時はidle状態に戻す
    };

    ws.onclose = () => {
        console.log('FastAPI WebSocket connection closed.');
        setMicState('idle'); // 切断時もidle状態に戻す
    }

    return () => {
      nestSocket.disconnect();
      ws.close();
      stopBrowserRecording(); // コンポーネント破棄時に録音停止
    };
  }, []); // 依存配列は空のまま

  const generateClientId = () => {
    return "client_" + Math.random().toString(36).substring(2, 15);
  };

  const speak = (text: string) => {
    setMicState('playing'); // 読み上げ開始時に状態を playing に変更
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ja-JP';
    utterance.onstart = () => {
        console.log("Speech synthesis started");
        setMicState('playing'); //念のためonstartでも設定
    };
    utterance.onend = () => {
      console.log("Speech synthesis ended");
      setMicState('idle'); // 読み上げ完了時に状態を idle に変更
    };
    utterance.onerror = (e) => {
        console.error("Speech synthesis error:", e);
        setMicState('idle'); // エラー時もidleに戻す
    }
    speechSynthesis.speak(utterance);
  };

  // ブラウザでの録音を開始する関数
  const startBrowserRecording = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error('getUserMedia not supported on your browser!');
      alert('お使いのブラウザは音声入力に対応していません。');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const context = new AudioContext();
      audioContextRef.current = context;
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1); // バッファサイズ、入力チャンネル数、出力チャンネル数
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (micState !== 'recording' || !fastAPIWebSocket || fastAPIWebSocket.readyState !== WebSocket.OPEN) {
          return;
        }
        // Float32Array を Int16Array に変換して送信
        const inputData = e.inputBuffer.getChannelData(0);
        const output = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            output[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF; // 16ビット整数に変換
        }
        // console.log("Sending audio data chunk..."); // ログが多いのでコメントアウト
        console.debug("送信前の音声データ（ArrayBufferサイズ）:", output.buffer.byteLength);
        fastAPIWebSocket.send(output.buffer);
      };

      source.connect(processor);
      processor.connect(context.destination); // プロセッサーを最終出力に接続（音を聞くわけではないが接続は必要）

      console.log("Browser recording started");

    } catch (err) {
      console.error('Error starting browser recording:', err);
      alert('マイクへのアクセス許可が必要です。');
      setMicState('idle'); // エラー時はidle状態に戻す
    }
  };

  // ブラウザでの録音を停止する関数
  const stopBrowserRecording = () => {
    console.log("Stopping browser recording...");
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null; // イベントリスナー解除
      processorRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        // AudioContextを閉じる前に少し待つ（エラー回避のため）
        setTimeout(() => {
            audioContextRef.current?.close().catch(e => console.error("Error closing AudioContext:", e));
            audioContextRef.current = null;
            console.log("AudioContext closed.");
        }, 100); // 100ms待つ
    }
  };

  // マイクボタンクリック時のハンドラ
  const handleMicClick = () => {
    if (micState === 'idle') {
      // 待機状態 -> 録音開始
      setMicState('recording');
      startBrowserRecording(); // ブラウザでの録音開始
      // FastAPI サーバーに録音開始を通知 (必要であればメッセージを送る)
      if (fastAPIWebSocket && fastAPIWebSocket.readyState === WebSocket.OPEN) {
          console.log("Sending start_recording signal to FastAPI");
          // 必要に応じて開始の合図を送る（例: JSONメッセージ）
          fastAPIWebSocket.send(JSON.stringify({ type: "start_recording" }));
      }

    } else if (micState === 'recording') {
      // 録音状態 -> 読み上げ準備/待機状態へ
      setMicState('idle'); // まずidleに戻し、FastAPIからの応答を待つ
      stopBrowserRecording(); // ブラウザでの録音停止
       // FastAPI サーバーに録音停止を通知（FastAPI側が音声データの終端を検知するなら不要な場合も）
      if (fastAPIWebSocket && fastAPIWebSocket.readyState === WebSocket.OPEN) {
          console.log("Sending stop_recording signal to FastAPI");
          // fastAPIWebSocket.send(JSON.stringify({ type: "stop_recording" }));
          // 空のデータを送ることで終端を示す場合もある
          fastAPIWebSocket.send(new ArrayBuffer(0));
      }
    } else if (micState === 'playing') {
        // 再生中 -> アイドル状態へ（再生停止）
        speechSynthesis.cancel(); // 現在の読み上げをキャンセル
        setMicState('idle');
        console.log("Speech synthesis cancelled by user.");
    }
  };

  // Lottieアニメーションのオプション
  const defaultOptions = {
    loop: true,
    autoplay: false, // micStateに応じて制御するのでautoplayはfalse
    animationData: animationData,
    rendererSettings: {
      preserveAspectRatio: 'xMidYMid slice'
    }
  };

  // ボタンの色を決定
  const getButtonColor = () => {
    switch (micState) {
      case 'recording':
        return 'red';
      case 'playing':
        return 'green';
      case 'idle':
      default:
        return 'blue';
    }
  };

  // 表示するメッセージを決定
  const getStatusMessage = () => {
    switch (micState) {
      case 'recording':
        return 'おはなしちゅう…';
      case 'playing':
        return 'おへんじちゅう…';
      case 'idle':
      default:
        return ''; // idle状態ではメッセージなし
    }
  };

  return (
    <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ width: '200px', height: '200px', marginBottom: '20px' }}>
        <Lottie
          options={defaultOptions}
          height={200}
          width={200}
          isStopped={micState !== 'playing'} // playing 状態でないときは停止
          isPaused={micState !== 'playing'}  // playing 状態でないときは一時停止
          ref={lottieRef}
        />
      </div>
      <button
        style={{
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          backgroundColor: getButtonColor(), // 状態に応じて色を変更
          border: 'none',
          color: 'white', // アイコンが見やすいように白文字に
          fontSize: '50px',
          cursor: 'pointer', // クリック可能を示すカーソル
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          transition: 'background-color 0.3s ease', // 色変化を滑らかに
        }}
        onClick={handleMicClick} // クリックイベントに変更
      >
        🎤
      </button>
      <p style={{ marginTop: '15px', height: '20px', color: '#555' }}> {/* メッセージ表示領域 */}
        {getStatusMessage()}
      </p>
    </div>
  );
}