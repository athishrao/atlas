from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import models
from app.database import get_db

router = APIRouter(tags=["redirect"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/{short}")
def redirect(short: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short=short.lower()).first()
    if not link:
        return templates.TemplateResponse("404.html", {"request": request, "short": short}, status_code=404)
    link.click_count += 1
    db.commit()
    if link.url.startswith("file://"):
        return templates.TemplateResponse("file_link.html", {"request": request, "link": link})
    return RedirectResponse(url=link.url, status_code=302)
