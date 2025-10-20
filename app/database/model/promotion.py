from sqlalchemy import String, TIMESTAMP, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    short_description: Mapped[str] = mapped_column(String, nullable=False)
    full_description: Mapped[str] = mapped_column(String, nullable=False)
    image_path: Mapped[str] = mapped_column(String, nullable=True)
    created_ad = mapped_column(TIMESTAMP, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)