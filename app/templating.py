from fastapi.templating import Jinja2Templates
from app.config import settings

templates = Jinja2Templates(directory="app/templates")
templates.env.globals.update(
    app_name=settings.app_name,
    prefix=settings.prefix,
    base_url=settings.base_url,
)
