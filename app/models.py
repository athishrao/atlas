from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    short: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    owner_email: Mapped[str] = mapped_column(String(255), nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Bundle(Base):
    __tablename__ = "bundles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    short: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    icon: Mapped[str] = mapped_column(String(10), default="📦")
    color: Mapped[str] = mapped_column(String(20), default="default")
    owner_email: Mapped[str] = mapped_column(String(255), nullable=False)
    visit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    items: Mapped[List["BundleItem"]] = relationship(
        "BundleItem", back_populates="bundle",
        order_by="BundleItem.position",
        cascade="all, delete-orphan"
    )


class BundleItem(Base):
    __tablename__ = "bundle_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bundle_id: Mapped[int] = mapped_column(Integer, ForeignKey("bundles.id"), nullable=False)
    link_short: Mapped[str] = mapped_column(String(50), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)

    bundle: Mapped["Bundle"] = relationship("Bundle", back_populates="items")
