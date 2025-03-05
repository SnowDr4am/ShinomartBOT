from sqlalchemy import Float, String, TIMESTAMP, Date, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import datetime


engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    registration_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)
    name: Mapped[str] = mapped_column(String)
    mobile_phone: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    birthday_date: Mapped[datetime .datetime] = mapped_column(Date, nullable=True)
    role: Mapped[str] = mapped_column(String) # Пользователь/Работник/Администратор

    purchase_history = relationship("PurchaseHistory", backref="user", lazy="dynamic")
    bonus_balance = relationship("UserBonusBalance", uselist=False, backref="user")

class PurchaseHistory(Base):
    __tablename__ = 'purchase_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    transaction_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)  # Тип транзакции (Пополнение/Списание)
    amount: Mapped[float] = mapped_column(Float, nullable=False) # Сумма покупки
    bonus_amount: Mapped[float] = mapped_column(Float, nullable=False) # Количество бонусов

class UserBonusBalance(Base):
    __tablename__ = 'user_bonus_balance'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0, nullable=False)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)