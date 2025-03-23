// frontend/src/app.module.ts
import { Module } from '@nestjs/common';
// import { AppController } from './app.controller'; // 削除
import { AppGateway } from './app.gateway';

@Module({
  imports: [],
  controllers: [], // AppController を削除
  providers: [AppGateway],
})
export class AppModule {}