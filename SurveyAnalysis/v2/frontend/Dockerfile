# Frontend Dockerfile for Google Cloud Run
# Multi-stage build for optimized production image

# Stage 1: Build
FROM node:18-alpine AS builder

# Build args (optional - can also use .env.production file)
ARG VITE_API_BASE_URL=""
ARG VITE_GOOGLE_CLIENT_ID=""

# Set env vars from build args if provided, otherwise Vite will read from .env.production
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code (including .env.production if it exists)
COPY . .

# Build the application (Vite will use ENV vars or .env.production file)
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

