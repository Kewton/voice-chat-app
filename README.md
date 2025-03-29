# frontend
## setup
```
npx create-next-app frontend
cd frontend

cd src
npm install @nestjs/platform-socket.io socket.io-client

npm install concurrently --save-dev
npm install @nestjs/cli --save-dev
```

# backend
```
mkdir backend
cd backend

python3 -m venv venv
source venv/bin/activate

brew install portaudio
pip install -r requirements.txt
```

# ToDo
- 機械的な音声でなくカッコ良い音声とする
- 音声入力モードを工夫
    - クリックすると赤色に変更し、音声での入力を受け付け
    - 音声を認識中はマイク入力っぽいメッセージ
    - クリックすると緑色に変更し、音声での出力
    - 音声での出力が終わると青色に変更