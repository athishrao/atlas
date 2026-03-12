import re
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import get_current_user, get_optional_user, require_owner_or_admin
from app.config import settings
from app.database import get_db
from app.templating import templates

router = APIRouter(tags=["bundles"])

SHORT_RE = re.compile(r"^[a-z0-9\-]{1,50}$")
COLORS = {"default", "cyan", "amber", "purple"}

def validate_bundle_short(short: str) -> str:
    short = short.lower()
    if not SHORT_RE.match(short):
        raise HTTPException(status_code=422, detail="Invalid short name.")
    if short in {"health", "api", "static", "bundles"}:
        raise HTTPException(status_code=422, detail=f"'{short}' is reserved.")
    return short

def _bundle_ctx(user, db):
    """Common template context extras."""
    return {"current_user": user, "admin_list": settings.admin_list}

def _resolve_items(link_shorts: list, db: Session):
    """Return BundleItem objects for a list of short names, skipping unknowns."""
    items = []
    for i, s in enumerate(link_shorts):
        s = s.strip().lower()
        if s and db.query(models.Link).filter_by(short=s).first():
            items.append(models.BundleItem(link_short=s, position=i))
    return items


# ── UI routes ──────────────────────────────────────────────────────────────

@router.get("/bundles")
def bundles_index(request: Request, user: Optional[str] = Depends(get_optional_user), db: Session = Depends(get_db)):
    bundles = db.query(models.Bundle).order_by(models.Bundle.name).all()
    # Attach resolved link objects for display
    all_links = {l.short: l for l in db.query(models.Link).all()}
    return templates.TemplateResponse("bundles.html", {
        "request": request,
        "bundles": bundles,
        "all_links": all_links,
        **_bundle_ctx(user, db),
    })

@router.get("/bundles/create")
def bundle_create_form(request: Request, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    all_links = db.query(models.Link).order_by(models.Link.short).all()
    return templates.TemplateResponse("bundle_create.html", {
        "request": request,
        "all_links": all_links,
        **_bundle_ctx(user, db),
    })

@router.post("/bundles/create")
def bundle_create_submit(
    request: Request,
    short: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    icon: str = Form("📦"),
    color: str = Form("default"),
    link_shorts: str = Form(""),   # comma-separated
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    short = validate_bundle_short(short)
    if db.query(models.Bundle).filter_by(short=short).first():
        raise HTTPException(status_code=409, detail="Bundle short name already taken.")
    if db.query(models.Link).filter_by(short=short).first():
        raise HTTPException(status_code=409, detail="A link with that short name already exists.")
    color = color if color in COLORS else "default"
    shorts = [s.strip() for s in link_shorts.split(",") if s.strip()]
    bundle = models.Bundle(short=short, name=name, description=description,
                           icon=icon, color=color, owner_email=user)
    bundle.items = _resolve_items(shorts, db)
    db.add(bundle)
    db.commit()
    return RedirectResponse(url="/bundles", status_code=303)

@router.get("/bundles/edit/{short}")
def bundle_edit_form(short: str, request: Request, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    bundle = db.query(models.Bundle).filter_by(short=short.lower()).first()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found.")
    require_owner_or_admin(user, bundle.owner_email)
    all_links = db.query(models.Link).order_by(models.Link.short).all()
    return templates.TemplateResponse("bundle_edit.html", {
        "request": request,
        "bundle": bundle,
        "all_links": all_links,
        "current_shorts": [item.link_short for item in bundle.items],
        **_bundle_ctx(user, db),
    })

@router.post("/bundles/edit/{short}")
def bundle_edit_submit(
    short: str,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    icon: str = Form("📦"),
    color: str = Form("default"),
    link_shorts: str = Form(""),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bundle = db.query(models.Bundle).filter_by(short=short.lower()).first()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found.")
    require_owner_or_admin(user, bundle.owner_email)
    color = color if color in COLORS else "default"
    shorts = [s.strip() for s in link_shorts.split(",") if s.strip()]
    bundle.name = name
    bundle.description = description
    bundle.icon = icon
    bundle.color = color
    bundle.items = _resolve_items(shorts, db)
    db.commit()
    return RedirectResponse(url="/bundles", status_code=303)

@router.post("/bundles/delete/{short}")
def bundle_delete(short: str, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    bundle = db.query(models.Bundle).filter_by(short=short.lower()).first()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found.")
    require_owner_or_admin(user, bundle.owner_email)
    db.delete(bundle)
    db.commit()
    return RedirectResponse(url="/bundles", status_code=303)


# ── API routes ─────────────────────────────────────────────────────────────

api_router = APIRouter(prefix="/api/bundles", tags=["bundles-api"])

@api_router.get("", response_model=list[schemas.BundleOut])
def api_list_bundles(db: Session = Depends(get_db)):
    return db.query(models.Bundle).order_by(models.Bundle.name).all()

@api_router.get("/{short}", response_model=schemas.BundleOut)
def api_get_bundle(short: str, db: Session = Depends(get_db)):
    bundle = db.query(models.Bundle).filter_by(short=short.lower()).first()
    if not bundle:
        raise HTTPException(status_code=404, detail="Not found.")
    return bundle
