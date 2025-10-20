from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import pytz
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.database.model import AsyncSessionLocal, Appointment

EKATERINBURG_TZ = pytz.timezone("Asia/Yekaterinburg")


def _to_tz(dt: Optional[datetime]) -> Optional[datetime]:
    """Привести datetime к Asia/Yekaterinburg (если naive — локализовать)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return EKATERINBURG_TZ.localize(dt)
    return dt.astimezone(EKATERINBURG_TZ)


class AppointmentService:
    # ---------- GET (Plural) ----------
    @classmethod
    async def get_appointments(
        cls,
        *,
        appointment_id: int | None = None,
        user_telegram_id: int | None = None,

        mobile_phone: str | None = None,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
        service: str | None = None,
        is_confirmed: bool | None = None,
        is_notified: bool | None = None,

        with_user: bool = False,

        limit: int | None = None,
        offset: int | None = None,
    ) -> List[Appointment]:
        async with AsyncSessionLocal() as session:
            stmt = select(Appointment)

            if with_user:
                stmt = stmt.options(selectinload(Appointment.user))

            tg_str: Optional[str] = str(user_telegram_id) if user_telegram_id is not None else None
            start_dt = _to_tz(start_datetime)
            end_dt = _to_tz(end_datetime)

            conditions = []
            if appointment_id is not None:
                conditions.append(Appointment.id == int(appointment_id))
            if tg_str is not None:
                conditions.append(Appointment.user_id == tg_str)
            if mobile_phone is not None:
                conditions.append(Appointment.mobile_phone == mobile_phone)
            if service is not None:
                conditions.append(Appointment.service == service)
            if is_confirmed is not None:
                conditions.append(Appointment.is_confirmed.is_(bool(is_confirmed)))
            if is_notified is not None:
                conditions.append(Appointment.is_notified.is_(bool(is_notified)))
            if start_dt is not None:
                conditions.append(Appointment.date_time >= start_dt)
            if end_dt is not None:
                conditions.append(Appointment.date_time < end_dt)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            stmt = stmt.order_by(Appointment.date_time.asc())

            if offset is not None:
                stmt = stmt.offset(int(offset))
            if limit is not None:
                stmt = stmt.limit(int(limit))

            res = await session.execute(stmt)
            return list(res.scalars().all())

    # ---------- GET (single) ----------
    @classmethod
    async def get_appointment(
        cls,
        **kwargs,
    ) -> Appointment | None:
        rows = await cls.get_appointments(limit=1, **kwargs)
        return rows[0] if rows else None

    # ---------- SAVE OR UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        appointment_id: int | None = None,
        user_telegram_id: int | None = None,

        mobile_phone: str | None = None,
        date_time: datetime | None = None,
        service: str | None = None,
        is_confirmed: bool | None = None,
        is_notified: bool | None = None,
    ) -> Appointment | None:
        # Нечем идентифицировать — ни id, ни пользователь
        if appointment_id is None and user_telegram_id is None:
            return None

        async with AsyncSessionLocal() as session:
            existing: Optional[Appointment] = None

            # 1) Пытаемся найти существующую запись
            if appointment_id is not None:
                q = select(Appointment).where(Appointment.id == int(appointment_id))
                existing = (await session.execute(q)).scalars().first()
            else:
                # По пользователю: сначала ближайшая будущая, затем любая
                now_ekb = datetime.now(EKATERINBURG_TZ)
                tg_str = str(user_telegram_id)

                q_future = (
                    select(Appointment)
                    .where(and_(Appointment.user_id == tg_str, Appointment.date_time >= now_ekb))
                    .order_by(Appointment.date_time.asc())
                )
                existing = (await session.execute(q_future)).scalars().first()
                if existing is None:
                    q_any = (
                        select(Appointment)
                        .where(Appointment.user_id == tg_str)
                        .order_by(Appointment.date_time.desc())
                    )
                    existing = (await session.execute(q_any)).scalars().first()

            # 2) Готовим patch из переданных полей (карта параметр -> поле модели)
            patch: dict = {}
            if mobile_phone is not None:
                patch["mobile_phone"] = mobile_phone
            if date_time is not None:
                patch["date_time"] = _to_tz(date_time)
            if service is not None:
                patch["service"] = service
            if is_confirmed is not None:
                patch["is_confirmed"] = bool(is_confirmed)
            if is_notified is not None:
                patch["is_notified"] = bool(is_notified)

            # 3) Если запись найдена — обновляем только переданные поля
            if existing is not None:
                if patch:
                    for k, v in patch.items():
                        setattr(existing, k, v)
                    await session.flush()
                await session.commit()
                return existing

            # 4) Если не нашли — создаём
            if user_telegram_id is None:
                # Для создания нужен пользователь
                return None
            if date_time is None:
                # Для новой записи обязательно нужно время записи
                return None
            if service is None:
                # Для новой записи нужна услуга
                return None
            if mobile_phone is None:
                # Лучше сразу сохранить телефон (по модели — NOT NULL)
                return None

            new_appointment = Appointment(
                user_id=str(user_telegram_id),
                mobile_phone=mobile_phone,
                date_time=_to_tz(date_time),
                service=service,
                is_confirmed=bool(is_confirmed) if is_confirmed is not None else False,
                is_notified=bool(is_notified) if is_notified is not None else False,
            )
            session.add(new_appointment)
            await session.flush()
            await session.commit()
            return new_appointment

    # ---------- DELETE ----------
    @classmethod
    async def delete(
        cls,
        *,
        appointment_id: int | None = None,
        user_telegram_id: int | None = None,
    ) -> bool:
        if appointment_id is None and user_telegram_id is None:
            return False

        async with AsyncSessionLocal() as session:
            target: Optional[Appointment] = None

            if appointment_id is not None:
                q = select(Appointment).where(Appointment.id == int(appointment_id))
                target = (await session.execute(q)).scalars().first()
            else:
                now_ekb = datetime.now(EKATERINBURG_TZ)
                tg_str = str(user_telegram_id)

                q_future = (
                    select(Appointment)
                    .where(and_(Appointment.user_id == tg_str, Appointment.date_time >= now_ekb))
                    .order_by(Appointment.date_time.asc())
                )
                target = (await session.execute(q_future)).scalars().first()
                if target is None:
                    q_any = (
                        select(Appointment)
                        .where(Appointment.user_id == tg_str)
                        .order_by(Appointment.date_time.desc())
                    )
                    target = (await session.execute(q_any)).scalars().first()

            if target is None:
                return False

            await session.delete(target)
            await session.commit()
            return True