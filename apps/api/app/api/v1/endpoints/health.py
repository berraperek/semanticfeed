from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version")
def version() -> dict[str, str | bool]:
    return {"version": settings.APP_VERSION, "debug": settings.DEBUG}
