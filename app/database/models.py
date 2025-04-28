from sqlalchemy import Float, String, TIMESTAMP, Date, Integer, ForeignKey, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import datetime

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3', echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    registration_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)
    name: Mapped[str] = mapped_column(String)
    mobile_phone: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    birthday_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    role: Mapped[str] = mapped_column(String)  # Пользователь/Работник/Администратор

    purchase_history = relationship("PurchaseHistory", back_populates="user", lazy="dynamic")
    bonus_balance = relationship("UserBonusBalance", uselist=False, back_populates="user")
    reviews = relationship("Review", back_populates="user", lazy="dynamic")
    appointments = relationship("Appointment", back_populates="user", lazy="dynamic")
    qr_codes = relationship("QRCode", back_populates="user")
    vote_history = relationship("VoteHistory", back_populates="user")
    vip_client = relationship("VipClient", back_populates="user", uselist=False)

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

class UserBonusBalance(Base):
    __tablename__ = 'user_bonus_balance'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    user = relationship("User", back_populates="bonus_balance")

class BonusSystem(Base):
    __tablename__ = 'bonus_system'

    id: Mapped[int] = mapped_column(primary_key=True)
    cashback: Mapped[int] = mapped_column(Integer, default=5)
    max_debit: Mapped[int] = mapped_column(Integer, default=30)
    start_bonus_balance: Mapped[int] = mapped_column(Integer, default=500)
    voting_bonus: Mapped[int] = mapped_column(Integer, default=100)
    vip_cashback: Mapped[int] = mapped_column(Integer, default=10)

class RoleHistory(Base):
    __tablename__ = 'role_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[str] = mapped_column(String, nullable=False)  # Кто выдал роль
    user_id: Mapped[str] = mapped_column(String, nullable=False)  # Кому выдал роль
    role: Mapped[str] = mapped_column(String, nullable=False)  # Какую роль выдал
    assigned_date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False)  # Дата выдачи роли

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

class Settings(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    daily_message_id: Mapped[int] = mapped_column(Integer, nullable=True)

class QRCode(Base):
    __tablename__ = 'qr_codes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    phone_number = mapped_column(String, nullable=False)
    created_at = mapped_column(TIMESTAMP, nullable=False)

    user = relationship("User", back_populates="qr_codes")

class VoteHistory(Base):
    __tablename__ = 'vote_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    data = mapped_column(TIMESTAMP, nullable=False)

    user = relationship("User", back_populates='vote_history')

class VipClient(Base):
    __tablename__ = "vip_clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="vip_client")

class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    short_description: Mapped[str] = mapped_column(String, nullable=False)
    full_description: Mapped[str] = mapped_column(String, nullable=False)
    image_path: Mapped[str] = mapped_column(String, nullable=True)
    created_ad = mapped_column(TIMESTAMP, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)