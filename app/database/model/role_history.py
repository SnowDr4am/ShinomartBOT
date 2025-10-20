from sqlalchemy import String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
import datetime

from .database import Base


class RoleHistory(Base):
    __tablename__ = 'role_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[str] = mapped_column(String, nullable=False)  # Кто выдал роль
    user_id: Mapped[str] = mapped_column(String, nullable=False)  # Кому выдал роль
    role: Mapped[str] = mapped_column(String, nullable=False)  # Какую роль выдал
    assigned_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)  # Дата выдачи роли