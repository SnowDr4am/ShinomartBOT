from __future__ import annotations

from typing import Optional, List
from datetime import datetime

import pytz
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.model import AsyncSessionLocal, VoteHistory, User

EKATERINBURG_TZ = pytz.timezone("Asia/Yekaterinburg")


def _now_utc() -> datetime:
    return datetime.now(EKATERINBURG_TZ).astimezone(pytz.UTC)


class VoteHistoryService:
    """Сервис для работы с историей голосований"""

    # ---------- GET (Plural) ----------
    @classmethod
    async def get_vote_histories(
        cls,
        *,
        vote_id: Optional[int] = None,
        user_pk: Optional[int] = None,           # PK User (VoteHistory.user_id)
        user_telegram_id: Optional[str] = None,  # User.user_id
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        with_user: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        newest_first: bool = True,
    ) -> List[VoteHistory]:
        async with AsyncSessionLocal() as session:
            stmt = select(VoteHistory)
            if with_user:
                stmt = stmt.options(selectinload(VoteHistory.user))

            if vote_id is not None:
                stmt = stmt.where(VoteHistory.id == vote_id)
            if user_pk is not None:
                stmt = stmt.where(VoteHistory.user_id == user_pk)
            if user_telegram_id is not None:
                stmt = stmt.join(User, User.id == VoteHistory.user_id).where(User.user_id == user_telegram_id)
            if date_from is not None:
                stmt = stmt.where(VoteHistory.data >= date_from)
            if date_to is not None:
                stmt = stmt.where(VoteHistory.data <= date_to)

            stmt = stmt.order_by(VoteHistory.data.desc() if newest_first else VoteHistory.data.asc())

            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())

    # ---------- GET (single) ----------
    @classmethod
    async def get_vote_history(cls, **kwargs) -> Optional[VoteHistory]:
        rows = await cls.get_vote_histories(limit=1, **kwargs)
        return rows[0] if rows else None

    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        vote_id: Optional[int] = None,
        user_telegram_id: Optional[str] = None,  # для создания ищем User по его TG id (User.user_id)
        user_pk: Optional[int] = None,           # альтернатива: передать PK User напрямую
        when: Optional[datetime] = None,         # дата голосования; по умолчанию — сейчас (UTC)
    ) -> VoteHistory:
        """
        Если vote_id передан — обновляет запись (меняет пользователя/дату, если указаны).
        Иначе создаёт новую запись голосования для найденного пользователя.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[VoteHistory] = None

                if vote_id is not None:
                    res = await session.execute(select(VoteHistory).where(VoteHistory.id == vote_id))
                    instance = res.scalars().first()
                    if instance is None:
                        raise ValueError("VoteHistory с таким id не найден")

                # определить пользователя
                user: Optional[User] = None
                if user_pk is not None or user_telegram_id is not None:
                    uq = select(User)
                    if user_pk is not None:
                        uq = uq.where(User.id == user_pk)
                    if user_telegram_id is not None:
                        uq = uq.where(User.user_id == user_telegram_id)
                    user = (await session.execute(uq)).scalars().first()
                    if user is None:
                        raise ValueError("Пользователь не найден")

                if instance is None:
                    if user is None:
                        raise ValueError("Для создания нужен пользователь (user_pk / user_telegram_id)")
                    instance = VoteHistory(
                        user_id=user.id,
                        data=when.astimezone(pytz.UTC) if when else _now_utc(),
                    )
                    session.add(instance)
                else:
                    if user is not None:
                        instance.user_id = user.id
                    if when is not None:
                        instance.data = when.astimezone(pytz.UTC)

            await session.refresh(instance)
            return instance