from fastapi import FastAPI
from app.config import settings
from app.database import Base, engine
from app import models  # noqa: ensure models are registered
from app.routes import links, ui, bundles, redirect

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(links.router)
app.include_router(ui.router)
app.include_router(bundles.router)
app.include_router(bundles.api_router)
app.include_router(redirect.router)  # always last

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}
