from fastapi import FastAPI
from src.core.config.settings import settings
from src.modules.document_analysis.document_analysis_router import router as document_analysis_router
from src.core.db.prisma import lifespan
from src.modules.sessions.router import router as sessions_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

    # Тестовый endpoint для проверки
    @app.get("/ping")
    async def ping():
        return {"status": "ok"}

    # Routers
    app.include_router(sessions_router, prefix=settings.FASTAPI_API_V1_PATH)

    # Register routers
    app.include_router(document_analysis_router, prefix=settings.FASTAPI_API_V1_PATH)

    return app
