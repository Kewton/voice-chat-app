import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.enableCors({
    origin: '*', // または ['http://127.0.0.1:3000'] など具体的なオリジン
  }); // CORSを有効化（開発用）
  await app.listen(3001); //Next.jsとは別のポートで起動
  console.log(`Nest Application is running on: ${await app.getUrl()}`);

}
bootstrap();