from fastapi import FastAPI

from app.api.router import router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Semantic search and an interest feed over new neuroscience preprints",
    version=settings.APP_VERSION,
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": settings.APP_NAME}
