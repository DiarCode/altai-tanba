from fastapi import FastAPI
from src.core.config.settings import settings
from src.modules.document_analysis_router import router as document_analysis_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0"
    )

    # Тестовый endpoint для проверки
    @app.get("/ping")
    async def ping():
        return {"status": "ok"}

    # Register routers
    app.include_router(document_analysis_router, prefix=settings.FASTAPI_API_V1_PATH)

    return app
