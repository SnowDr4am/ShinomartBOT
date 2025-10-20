from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserBonusBalance(Base):
    __tablename__ = 'user_bonus_balance'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    user = relationship("User", back_populates="bonus_balance")