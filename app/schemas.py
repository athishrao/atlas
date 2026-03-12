from datetime import datetime
from typing import Optional, List
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


# Bundle schemas
class BundleCreate(BaseModel):
    short: str
    name: str
    description: str = ""
    icon: str = "📦"
    color: str = "default"
    link_shorts: List[str] = []

class BundleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    link_shorts: Optional[List[str]] = None

class BundleItemOut(BaseModel):
    link_short: str
    position: int

    class Config:
        from_attributes = True

class BundleOut(BaseModel):
    id: int
    short: str
    name: str
    description: str
    icon: str
    color: str
    owner_email: str
    visit_count: int
    created_at: datetime
    updated_at: datetime
    items: List[BundleItemOut] = []

    class Config:
        from_attributes = True
