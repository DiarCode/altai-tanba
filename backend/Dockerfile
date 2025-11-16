FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies for PyTorch, OpenCV, and OCR/PDF tooling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        git \
        curl \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate the Prisma client used by the FastAPI application
RUN prisma generate

# Runtime configuration (build arguments -> environment variables)
ARG APP_NAME=AltaiTanba
ARG APP_ENV=development
ARG FASTAPI_API_V1_PATH=/api/v1

ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME
ARG DB_PORT
ARG DB_HOST
ARG PG_EMAIL
ARG PG_PASSWORD
ARG DATABASE_URL

ARG SECURITY_BACKEND_CORS_ORIGINS
ARG SECURITY_ALLOWED_HOSTS
ARG SERVER_PORT=8080
ARG USE_STUB_ADAPTER=false

ARG S3_ACCESS_ENDPOINT
ARG S3_RESPONSE_ENDPOINT
ARG S3_REGION
ARG S3_ACCESS_KEY
ARG S3_SECRET_KEY
ARG S3_BUCKET
ARG S3_IMAGE_PREFIX
ARG S3_AUDIO_PREFIX
ARG S3_PATH_STYLE=true

ARG MODAL_LLM_ENDPOINT
ARG MODAL_OCR_ENDPOINT
ARG USE_MODAL_OCR=true

ENV APP_NAME=${APP_NAME} \
    APP_ENV=${APP_ENV} \
    FASTAPI_API_V1_PATH=${FASTAPI_API_V1_PATH} \
    DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    DB_NAME=${DB_NAME} \
    DB_PORT=${DB_PORT} \
    DB_HOST=${DB_HOST} \
    PG_EMAIL=${PG_EMAIL} \
    PG_PASSWORD=${PG_PASSWORD} \
    DATABASE_URL=${DATABASE_URL} \
    SECURITY_BACKEND_CORS_ORIGINS=${SECURITY_BACKEND_CORS_ORIGINS} \
    SECURITY_ALLOWED_HOSTS=${SECURITY_ALLOWED_HOSTS} \
    SERVER_PORT=${SERVER_PORT} \
    USE_STUB_ADAPTER=${USE_STUB_ADAPTER} \
    S3_ACCESS_ENDPOINT=${S3_ACCESS_ENDPOINT} \
    S3_RESPONSE_ENDPOINT=${S3_RESPONSE_ENDPOINT} \
    S3_REGION=${S3_REGION} \
    S3_ACCESS_KEY=${S3_ACCESS_KEY} \
    S3_SECRET_KEY=${S3_SECRET_KEY} \
    S3_BUCKET=${S3_BUCKET} \
    S3_IMAGE_PREFIX=${S3_IMAGE_PREFIX} \
    S3_AUDIO_PREFIX=${S3_AUDIO_PREFIX} \
    S3_PATH_STYLE=${S3_PATH_STYLE} \
    MODAL_LLM_ENDPOINT=${MODAL_LLM_ENDPOINT} \
    MODAL_OCR_ENDPOINT=${MODAL_OCR_ENDPOINT} 

EXPOSE 8080

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${SERVER_PORT:-8080}"]
