from fastapi import FastAPI
from app.config import settings
from app.database import Base, engine
from app import models  # noqa: ensure models are registered

app = FastAPI(title="tn-links", debug=settings.debug)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}
