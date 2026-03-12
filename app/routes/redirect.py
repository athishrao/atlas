from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.templating import templates

router = APIRouter(tags=["redirect"])

@router.get("/{short}")
def redirect(short: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short=short.lower()).first()
    if not link:
        return RedirectResponse(url=f"/?q={short.lower()}", status_code=302)
    link.click_count += 1
    db.commit()
    if link.url.startswith("file://"):
        return templates.TemplateResponse("file_link.html", {"request": request, "link": link})
    return RedirectResponse(url=link.url, status_code=302)
