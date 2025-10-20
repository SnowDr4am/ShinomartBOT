from sqlalchemy import Float, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

from .database import Base


class PurchaseHistory(Base):
    __tablename__ = 'purchase_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    worker_id: Mapped[str] = mapped_column(String, nullable=False)
    transaction_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)  # Пополнение/Списание
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Сумма покупки
    bonus_amount: Mapped[float] = mapped_column(Float, nullable=False)  # Количество бонусов

    user = relationship("User", back_populates="purchase_history")
    reviews = relationship("Review", back_populates="purchase", lazy="dynamic")