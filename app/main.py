from fastapi import FastAPI
from app.config import settings

app = FastAPI(title="tn-links", debug=settings.debug)

@app.get("/health")
def health():
    return {"status": "ok"}
