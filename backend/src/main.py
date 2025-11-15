from src.app_module import create_app 
from src.core.config.settings import settings
import uvicorn
from fastapi import FastAPI

app: FastAPI = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",           
        host="0.0.0.0",
        port=settings.SERVER_PORT,
        reload=True
    )
