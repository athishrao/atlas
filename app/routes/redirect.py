from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.templating import templates

router = APIRouter(tags=["redirect"])

@router.get("/{short}")
def redirect(short: str, request: Request, db: Session = Depends(get_db)):
    short = short.lower()

    # 1. Check regular links
    link = db.query(models.Link).filter_by(short=short).first()
    if link:
        link.click_count += 1
        db.commit()
        if link.url.startswith("file://"):
            return templates.TemplateResponse("file_link.html", {"request": request, "link": link})
        return RedirectResponse(url=link.url, status_code=302)

    # 2. Check bundles
    bundle = db.query(models.Bundle).filter_by(short=short).first()
    if bundle:
        bundle.visit_count += 1
        db.commit()
        all_links = {l.short: l for l in db.query(models.Link).all()}
        return templates.TemplateResponse("bundle_landing.html", {
            "request": request,
            "bundle": bundle,
            "all_links": all_links,
        })

    # 3. Not found — search fallback
    return RedirectResponse(url=f"/?q={short}", status_code=302)
