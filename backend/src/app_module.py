from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from src.core.config.settings import settings
from src.modules.document_analysis.document_analysis_router import router as document_analysis_router
from src.modules.chat.chat_router import router as chat_router
from src.core.db.prisma import lifespan
from src.modules.sessions.router import router as sessions_router


def _split_env_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

    allowed_origins = _split_env_list(settings.SECURITY_BACKEND_CORS_ORIGINS)
    allowed_hosts = _split_env_list(settings.SECURITY_ALLOWED_HOSTS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # Тестовый endpoint для проверки
    @app.get("/ping")
    async def ping():
        return {"status": "ok"}

    # Routers
    app.include_router(sessions_router, prefix=settings.FASTAPI_API_V1_PATH)

    # Register routers
    app.include_router(document_analysis_router, prefix=settings.FASTAPI_API_V1_PATH)
    app.include_router(chat_router, prefix=settings.FASTAPI_API_V1_PATH)

    return app
