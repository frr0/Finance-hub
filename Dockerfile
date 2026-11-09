# Stage 1: Build Frontend Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npx vite build

# Stage 2: Production Python Backend + Static UI
FROM python:3.12-slim
WORKDIR /app

# Install runtime dependencies (OpenSSH for SSH sync)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend application
COPY backend/app /app/app

# Copy compiled frontend from Stage 1
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_DIR=/app/data
ENV FRONTEND_DIST=/app/frontend/dist
ENV FIREFLY_SQL_PATH=/app/firefly_reference/init.sql

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
