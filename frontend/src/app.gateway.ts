// frontend/src/app.gateway.ts
import {
  WebSocketGateway,
  SubscribeMessage,
  MessageBody,
  WebSocketServer,
  ConnectedSocket,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';

@WebSocketGateway({
  cors: {
    origin: '*', // 開発環境。本番環境では適切なオリジンを設定
  },
  namespace: 'voice-chat', // 名前空間を設定 (任意)
})
export class AppGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server: Server | null = null;

  handleConnection(client: Socket) {
    console.log(`Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`Client disconnected: ${client.id}`);
  }

  @SubscribeMessage('start_recording')
  handleStartRecording(@ConnectedSocket() client: Socket) { // data 引数を削除
      console.log(`Start recording requested by client: ${client.id}`);
  }

    @SubscribeMessage('message')
    handleMessage(@ConnectedSocket() client: Socket, @MessageBody() payload: unknown): string { // 型を unknown に
      console.log("message", payload)
    return 'Hello world!';
  }
}