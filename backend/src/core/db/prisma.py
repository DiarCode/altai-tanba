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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    try:
        yield
    finally:
        await disconnect()
