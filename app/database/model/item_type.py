from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ItemType(Base):
    __tablename__ = "item_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[str] = mapped_column(String)

    categories = relationship("Category", back_populates="item_type")
