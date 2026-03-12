import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import get_current_user, require_owner_or_admin
from app.database import get_db

router = APIRouter(prefix="/api/links", tags=["links"])

SHORT_RE = re.compile(r"^[a-z0-9\-]{1,50}$")

def validate_short(short: str) -> str:
    short = short.lower()
    if not SHORT_RE.match(short):
        raise HTTPException(status_code=422, detail="Invalid short name. Use lowercase alphanumeric and hyphens, 1-50 chars.")
    reserved = {"health", "api", "static"}
    if short in reserved:
        raise HTTPException(status_code=422, detail=f"'{short}' is a reserved name.")
    return short

@router.get("", response_model=list[schemas.LinkOut])
def list_links(q: Optional[str] = Query(None), skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(models.Link)
    if q:
        query = query.filter(
            models.Link.short.contains(q) |
            models.Link.description.contains(q) |
            models.Link.owner_email.contains(q)
        )
    return query.order_by(models.Link.short).offset(skip).limit(limit).all()

@router.post("", response_model=schemas.LinkOut, status_code=201)
def create_link(payload: schemas.LinkCreate, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    short = validate_short(payload.short)
    if db.query(models.Link).filter_by(short=short).first():
        raise HTTPException(status_code=409, detail="Short name already taken.")
    link = models.Link(short=short, url=str(payload.url), description=payload.description, owner_email=user)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

@router.get("/{short}", response_model=schemas.LinkOut)
def get_link(short: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short=short.lower()).first()
    if not link:
        raise HTTPException(status_code=404, detail="Not found.")
    return link

@router.put("/{short}", response_model=schemas.LinkOut)
def update_link(short: str, payload: schemas.LinkUpdate, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short=short.lower()).first()
    if not link:
        raise HTTPException(status_code=404, detail="Not found.")
    require_owner_or_admin(user, link.owner_email)
    if payload.url:
        link.url = str(payload.url)
    if payload.description is not None:
        link.description = payload.description
    db.commit()
    db.refresh(link)
    return link

@router.delete("/{short}", status_code=204)
def delete_link(short: str, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short=short.lower()).first()
    if not link:
        raise HTTPException(status_code=404, detail="Not found.")
    require_owner_or_admin(user, link.owner_email)
    db.delete(link)
    db.commit()
