# Dockerfile for Next.js Frontend with integrated NestJS WebSocket server

# ---- Base Stage ----
# Use an official Node.js runtime as a parent image
FROM node:20-alpine AS base
WORKDIR /app

# ---- Dependencies Stage ----
FROM base AS deps
# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
# Prefer 'npm ci' for reproducible installs in CI/CD environments
RUN npm ci

# ---- Builder Stage ----
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variable for production build
ENV NODE_ENV=production

# Build NestJS part (assuming source is in 'src' and output is 'dist')
# Ensure tsconfig.build.json outputs to './dist'
RUN npm run build:nest

# Build Next.js part
RUN npm run build -- --no-lint
# 'npm run build' in the provided package.json runs 'nest build'.
# Assuming the user wants to build both NestJS and Next.js for production.
# We need to explicitly run Next.js build as well.
# If `npm run build` should handle both, update the script in package.json.
# For now, we run `next build` directly.
RUN npx next build

# ---- Runner Stage ----
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
# Uncomment the following line in case you want to disable telemetry during runtime.
# ENV NEXT_TELEMETRY_DISABLED 1

# Copy necessary files from the builder stage
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Copy NestJS build output
COPY --from=builder /app/dist ./dist

# Copy Next.js build output
COPY --from=builder --chown=node:node /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.mjs ./next.config.mjs

# Expose the ports Next.js (3000) and NestJS (3001) run on
EXPOSE 3000 3001

# User and group for security (optional but recommended)
# USER node

# Command to run both NestJS and Next.js servers
# Runs NestJS server in the background and starts Next.js server in the foreground
CMD ["sh", "-c", "node dist/main.js & npm start"]
# Note: `npm start` runs `next start` based on the package.json