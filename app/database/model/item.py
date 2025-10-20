from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)

    value: Mapped[str] = mapped_column(String, nullable=False)
    meta_data: Mapped[dict] = mapped_column(JSON, default={})

    category = relationship("Category", back_populates="items")