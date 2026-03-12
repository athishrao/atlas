from datetime import datetime
from typing import Optional
from pydantic import BaseModel, AnyUrl

class LinkCreate(BaseModel):
    short: str
    url: AnyUrl
    description: str = ""

class LinkUpdate(BaseModel):
    url: Optional[AnyUrl] = None
    description: Optional[str] = None

class LinkOut(BaseModel):
    id: int
    short: str
    url: str
    description: str
    owner_email: str
    click_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
