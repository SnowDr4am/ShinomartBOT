from sqlalchemy import String, TIMESTAMP, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

from .database import Base


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    purchase_id: Mapped[int] = mapped_column(ForeignKey('purchase_history.id'), nullable=False)  # Связь с транзакцией
    worker_id: Mapped[str] = mapped_column(String, nullable=False)  # Работник, которого оценивают
    review_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # Оценка от 1 до 5
    comment: Mapped[str] = mapped_column(String, nullable=True)  # Комментарий (опционально)

    user = relationship("User", back_populates="reviews")
    purchase = relationship("PurchaseHistory", back_populates="reviews")