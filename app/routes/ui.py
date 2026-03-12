from typing import Optional
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import models
from app.auth import get_current_user, get_optional_user, require_owner_or_admin
from app.config import settings
from app.database import get_db
from app.templating import templates

router = APIRouter(tags=["ui"])

@router.get("/")
def index(request: Request, q: str = "", user: Optional[str] = Depends(get_optional_user), db: Session = Depends(get_db)):
    links = db.query(models.Link).order_by(models.Link.short).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "links": links,
        "q": q,
        "current_user": user,
        "link_count": len(links),
        "admin_list": settings.admin_list,
    })

@router.get("/create")
def create_form(request: Request, short: str = "", user: Optional[str] = Depends(get_optional_user)):
    return templates.TemplateResponse("create.html", {
        "request": request,
        "short": short,
        "current_user": user,
        "admin_list": settings.admin_list,
    })

@router.post("/create")
def create_submit(
    request: Request,
    short: str = Form(...),
    url: str = Form(...),
    description: str = Form(""),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    short = short.lower()
    if db.query(models.Link).filter_by(short=short).first():
        return templates.TemplateResponse("create.html", {
            "request": request,
            "short": short,
            "url": url,
            "description": description,
            "error": f"'{short}' is already taken.",
            "current_user": user,
            "admin_list": settings.admin_list,
        }, status_code=409)
    link = models.Link(short=short, url=url, description=description, owner_email=user)
    db.add(link)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.get("/edit/{short}")
def edit_form(short: str, request: Request, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short=short).first()
    require_owner_or_admin(user, link.owner_email)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "link": link,
        "current_user": user,
        "admin_list": settings.admin_list,
    })

@router.post("/edit/{short}")
def edit_submit(
    short: str,
    request: Request,
    url: str = Form(...),
    description: str = Form(""),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(models.Link).filter_by(short=short).first()
    require_owner_or_admin(user, link.owner_email)
    link.url = url
    link.description = description
    db.commit()
    return RedirectResponse(url="/", status_code=303)
