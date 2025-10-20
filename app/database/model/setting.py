from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Settings(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    daily_message_id: Mapped[int] = mapped_column(Integer, nullable=True)