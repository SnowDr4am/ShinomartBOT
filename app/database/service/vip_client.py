from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select, delete, or_
from sqlalchemy.orm import selectinload

from app.database.model import AsyncSessionLocal, VipClient, User


class VipClientService:
    """Сервис для работы с VIP-клиентами"""

    # ---------- GET (Plural) ----------
    @classmethod
    async def get_vip_clients(
        cls,
        *,
        vip_id: Optional[int] = None,
        user_id: Optional[int] = None,          # PK из таблицы User
        user_telegram_id: Optional[str] = None, # User.user_id (строка TG)
        phone_number: Optional[str] = None,
        with_user: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[VipClient]:
        async with AsyncSessionLocal() as session:
            stmt = select(VipClient)
            if with_user:
                stmt = stmt.options(selectinload(VipClient.user))

            if vip_id is not None:
                stmt = stmt.where(VipClient.id == vip_id)
            if user_id is not None:
                stmt = stmt.where(VipClient.user_id == user_id)

            # фильтры по связанному User
            user_subconds = []
            if user_telegram_id is not None:
                user_subconds.append(User.user_id == user_telegram_id)
            if phone_number is not None:
                user_subconds.append(User.mobile_phone == phone_number)
            if user_subconds:
                stmt = stmt.join(User, User.id == VipClient.user_id).where(or_(*user_subconds))

            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())

    # ---------- GET (single) ----------
    @classmethod
    async def get_vip_client(cls, **kwargs) -> Optional[VipClient]:
        rows = await cls.get_vip_clients(limit=1, **kwargs)
        return rows[0] if rows else None

    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        vip_id: Optional[int] = None,
        # как найти/создать по пользователю:
        user_id: Optional[int] = None,            # PK User
        user_telegram_id: Optional[str] = None,   # User.user_id (строка)
        phone_number: Optional[str] = None,       # User.mobile_phone
    ) -> VipClient:
        """
        Если передан vip_id — ничего, кроме привязки к user, менять особо не о чем.
        Без vip_id: создаёт VIP для найденного пользователя (если ещё нет).
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[VipClient] = None

                # UPDATE по vip_id
                if vip_id is not None:
                    res = await session.execute(select(VipClient).where(VipClient.id == vip_id))
                    instance = res.scalars().first()
                    if instance is None:
                        raise ValueError("VipClient с таким id не найден")

                # Определим пользователя
                user: Optional[User] = None
                if user_id is not None or user_telegram_id is not None or phone_number is not None:
                    uq = select(User)
                    if user_id is not None:
                        uq = uq.where(User.id == user_id)
                    if user_telegram_id is not None:
                        uq = uq.where(User.user_id == user_telegram_id)
                    if phone_number is not None:
                        uq = uq.where(User.mobile_phone == phone_number)
                    user = (await session.execute(uq)).scalars().first()

                    if user is None:
                        raise ValueError("Пользователь не найден по заданным критериям")

                # Создание, если нет существующей записи
                if instance is None:
                    if user is None:
                        raise ValueError("Нужно указать пользователя (user_id / user_telegram_id / phone_number)")
                    # проверим, что у него ещё нет VIP
                    exists = (
                        await session.execute(select(VipClient).where(VipClient.user_id == user.id))
                    ).scalars().first()
                    if exists:
                        instance = exists
                    else:
                        instance = VipClient(user_id=user.id)
                        session.add(instance)
                else:
                    # Обновление привязки к пользователю (редкий кейс)
                    if user is not None:
                        instance.user_id = user.id

            await session.refresh(instance)
            return instance

    # ---------- DELETE ----------
    @classmethod
    async def delete(
        cls,
        *,
        vip_id: Optional[int] = None,
        user_id: Optional[int] = None,
        user_telegram_id: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> bool:
        """
        Удаление VIP-записи:
        - по vip_id, или
        - по пользователю (user_id / user_telegram_id / phone_number).
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                if vip_id is not None:
                    res = await session.execute(delete(VipClient).where(VipClient.id == vip_id))
                    affected = getattr(res, "rowcount", None)
                    return bool(affected and affected > 0)

                # найти user.id
                uq = select(User)
                if user_id is not None:
                    uq = uq.where(User.id == user_id)
                if user_telegram_id is not None:
                    uq = uq.where(User.user_id == user_telegram_id)
                if phone_number is not None:
                    uq = uq.where(User.mobile_phone == phone_number)
                user = (await session.execute(uq)).scalars().first()
                if not user:
                    return False

                res = await session.execute(delete(VipClient).where(VipClient.user_id == user.id))
                affected = getattr(res, "rowcount", None)
                return bool(affected and affected > 0)