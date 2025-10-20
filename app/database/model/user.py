from sqlalchemy import String, TIMESTAMP, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

from .database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    registration_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)
    name: Mapped[str] = mapped_column(String)
    mobile_phone: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    birthday_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    role: Mapped[str] = mapped_column(String)  # Пользователь/Работник/Администратор

    purchase_history = relationship("PurchaseHistory", back_populates="user", lazy="selectin")
    bonus_balance = relationship("UserBonusBalance", uselist=False, back_populates="user")
    reviews = relationship("Review", back_populates="user", lazy="selectin")
    appointments = relationship("Appointment", back_populates="user", lazy="selectin")
    qr_codes = relationship("QRCode", back_populates="user")
    vote_history = relationship("VoteHistory", back_populates="user")
    vip_client = relationship("VipClient", back_populates="user", uselist=False)