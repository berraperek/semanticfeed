from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI system for managing information overload",
    version=settings.APP_VERSION,
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": settings.APP_NAME}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str | bool]:
    return {
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }