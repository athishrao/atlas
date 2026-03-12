from typing import Optional
from fastapi import Header, HTTPException
from app.config import settings

def get_current_user(x_forwarded_user: Optional[str] = Header(default=None)) -> str:
    if not x_forwarded_user:
        if settings.debug:
            return "dev@localhost"
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_forwarded_user

def get_optional_user(x_forwarded_user: Optional[str] = Header(default=None)) -> Optional[str]:
    if not x_forwarded_user:
        if settings.debug:
            return "dev@localhost"
        return None
    return x_forwarded_user

def require_owner_or_admin(email: str, owner_email: str):
    if email != owner_email and email not in settings.admin_list:
        raise HTTPException(status_code=403, detail="Forbidden")
