from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[str] = mapped_column(String)
    type_id: Mapped[int] = mapped_column(ForeignKey("item_types.id"))

    item_type = relationship("ItemType", back_populates="categories")
    items = relationship("Item", back_populates="category")