from fastapi import FastAPI

app = FastAPI(
    title="SemanticFeed API",
    description="AI system for managing information overload",
    version="0.1.0"
)


@app.get("/")
def root():
    return {"message": "SemanticFeed API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": "0.1.0"}