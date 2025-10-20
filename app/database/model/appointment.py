from sqlalchemy import String, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

from .database import Base


class Appointment(Base):
    __tablename__ = 'appointments'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=False)  # Связь с users.user_id
    mobile_phone: Mapped[str] = mapped_column(String, nullable=False)  # Телефон пользователя
    date_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)  # Дата и время записи
    service: Mapped[str] = mapped_column(String, nullable=False)  # Название услуги
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)  # Статус подтверждения
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False)  # Статус уведомления

    user = relationship("User", back_populates="appointments")  # Связь с моделью User