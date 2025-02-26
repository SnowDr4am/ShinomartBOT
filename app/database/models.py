from enum import unique

from sqlalchemy import Float, String, TIMESTAMP, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
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
    birthday_date: Mapped[datetime.datetime] = mapped_column(Date, nullable=True)
    role: Mapped[str] = mapped_column(String)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)