from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class BonusSystem(Base):
    __tablename__ = 'bonus_system'

    id: Mapped[int] = mapped_column(primary_key=True)
    cashback: Mapped[int] = mapped_column(Integer, default=5)
    max_debit: Mapped[int] = mapped_column(Integer, default=30)
    start_bonus_balance: Mapped[int] = mapped_column(Integer, default=500)
    voting_bonus: Mapped[int] = mapped_column(Integer, default=100)
    vip_cashback: Mapped[int] = mapped_column(Integer, default=10)