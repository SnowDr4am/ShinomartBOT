from sqlalchemy import select
from datetime import datetime, timedelta
from app.database.models import async_session
from app.database.models import Appointment
import pytz


async def check_availability(date_time: datetime) -> bool:
    """Проверяет, свободно ли время с окном в 1 час от указанного."""
    async with async_session() as session:
        start_time = date_time
        end_time = date_time + timedelta(hours=1)

        stmt = select(Appointment).where(
            (Appointment.date_time.between(start_time, end_time - timedelta(minutes=1))) |
            ((Appointment.date_time < start_time) & (Appointment.date_time + timedelta(hours=1) > start_time))
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()

        return existing is None


async def get_active_appointment(user_id: str) -> Appointment | None:
    """Возвращает активную запись пользователя (в будущем), если она есть."""
    async with async_session() as session:
        current_time = datetime.now(tz=pytz.timezone('Asia/Yekaterinburg'))
        stmt = select(Appointment).where(
            (Appointment.user_id == user_id) &
            (Appointment.date_time > current_time)
        )
        result = await session.execute(stmt)
        appointment = result.scalars().first()

        return appointment


async def add_appointment(user_id: str, date_time: datetime, service: str, mobile_phone: str) -> Appointment | None:
    """Добавляет запись в БД, если у пользователя нет активных записей."""
    async with async_session() as session:
        appointment = Appointment(
            user_id=user_id,
            date_time=date_time,
            service=service,
            mobile_phone=mobile_phone
        )
        session.add(appointment)
        await session.commit()

        return appointment


async def cancel_appointment(user_id) -> bool:
    """Удаляет активную запись пользователя из БД по user_id."""
    async with async_session() as session:
        appointment = await session.scalar(
            select(Appointment)
            .where(Appointment.user_id==user_id)
        )
        if appointment:
            await session.delete(appointment)
            await session.commit()

            return True
        return False


async def find_next_available_time(desired_time: datetime) -> datetime:
    """Находит ближайшее свободное время после указанного с шагом 1 час."""
    async with async_session() as session:
        current_time = desired_time
        while True:
            current_time += timedelta(hours=1)
            if current_time.hour >= 21:
                current_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
            if current_time.hour < 9:
                current_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
            if await check_availability(current_time):
                return current_time