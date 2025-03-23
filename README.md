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
