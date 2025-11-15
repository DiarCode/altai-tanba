from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prisma import Prisma

# Global prisma instance for simple usage in request handlers
prisma = Prisma()


async def connect() -> None:
    if not prisma.is_connected():
        await prisma.connect()


async def disconnect() -> None:
    if prisma.is_connected():
        await prisma.disconnect()


async def get_db() -> Prisma:
    # На всякий случай гарантируем, что подключен
    await connect()
    return prisma

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect()
    
    # Pre-initialize OCR service to avoid delays on first request
    print("Pre-initializing OCR service...")
    from src.core.services.ocr_service import ocr_service
    ocr_service._ensure_reader()
    print("OCR service ready.")
    
    try:
        yield
    finally:
        # Shutdown
        await disconnect()
