import re
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import get_current_user, require_owner_or_admin
from app.database import get_db

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def index(request: Request, q: str = "", db: Session = Depends(get_db)):
    query = db.query(models.Link)
    if q:
        query = query.filter(
            models.Link.short.contains(q) |
            models.Link.description.contains(q)
        )
    links = query.order_by(models.Link.short).all()
    return templates.TemplateResponse("index.html", {"request": request, "links": links, "q": q})

@router.get("/create")
def create_form(request: Request, short: str = ""):
    return templates.TemplateResponse("create.html", {"request": request, "short": short})

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
    link = models.Link(short=short, url=url, description=description, owner_email=user)
    db.add(link)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.get("/edit/{short}")
def edit_form(short: str, request: Request, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short=short).first()
    require_owner_or_admin(user, link.owner_email)
    return templates.TemplateResponse("edit.html", {"request": request, "link": link})

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
