from fastapi import FastAPI

from app.config import get_settings
from app.routers import auth

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(auth.router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TaskFlow API is running", "environment": settings.environment}
