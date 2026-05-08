from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI system for managing information overload",
    version=settings.APP_VERSION,
)


@app.get("/")
def root():
    return {"message": settings.APP_NAME}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }