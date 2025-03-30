This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Environment Variables

This application uses environment variables to configure WebSocket server URLs.

-   `NEXT_PUBLIC_NESTJS_WS_URL`: The URL for the NestJS WebSocket server (integrated within this project).
    -   **Development (`.env.local`)**: `ws://127.0.0.1:3001/voice-chat` (or similar)
    -   **Production (`docker-compose.yml`)**: `ws://localhost:3001/voice-chat` (when accessing from the browser on the host machine)
-   `NEXT_PUBLIC_FASTAPI_WS_URL`: The base URL for the FastAPI WebSocket server (external service).
    -   **Development (`.env.local`)**: `ws://127.0.0.1:5000/ws/` (or the actual host/port where FastAPI runs)
    -   **Production (`docker-compose.yml`)**: Needs to be set according to where the FastAPI server is accessible from the user's browser relative to the container. Examples:
        -   `ws://host.docker.internal:5000/ws/` (Docker Desktop accessing host)
        -   `ws://<host-ip>:5000/ws/`
        -   `ws://fastapi_service_name:5000/ws/` (If FastAPI runs in another Docker Compose service)

**Note:** Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

### Setting Environment Variables

-   **Development:** Create a `.env.local` file in the project root and define the variables there. This file is not committed to Git.
-   **Production (Docker Compose):** Define the variables under the `environment` section in the `docker-compose.yml` file.

## Containerization (Docker)

You can build and run this application using Docker and Docker Compose.

### Building the Docker Image

To build the Docker image locally:

```bash
docker build -t voice-chat-frontend .
```
### Running the Container Directly
To run the built image as a container:

```bash
# Replace <nestjs-ws-url> and <fastapi-ws-url> with appropriate values for your environment
docker run -d \
  -p 3000:3000 \
  -p 3001:3001 \
  -e NODE_ENV=production \
  -e NEXT_PUBLIC_NESTJS_WS_URL="ws://localhost:3001/voice-chat" \
  -e NEXT_PUBLIC_FASTAPI_WS_URL="ws://host.docker.internal:5000/ws/" \
  --name my-voice-chat-app \
  voice-chat-frontend
```
Explanation:

-d: Run in detached mode.<br>
-p 3000:3000: Map host port 3000 to container port 3000 (Next.js).<br>
-p 3001:3001: Map host port 3001 to container port 3001 (NestJS).<br>
-e: Set environment variables. Adjust URLs as needed.<br>
--name: Assign a name to the container.<br>

### Running with Docker Compose
The recommended way to run the application in a containerized environment is using Docker Compose. It uses the docker-compose.yml file for configuration.
```bash
# Build and start the services in detached mode
docker-compose up --build -d

# To stop the services
docker-compose down
```