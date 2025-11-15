from fastapi import FastAPI
from src.core.config.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0"
    )

    # Тестовый endpoint для проверки
    @app.get("/ping")
    async def ping():
        return {"status": "ok"}

    return app
