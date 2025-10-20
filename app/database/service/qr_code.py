from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timedelta

import pytz
from sqlalchemy import select

from app.database.model import AsyncSessionLocal, QRCode


EKATERINBURG_TZ = pytz.timezone("Asia/Yekaterinburg")


def _now_utc() -> datetime:
    return datetime.now(EKATERINBURG_TZ).astimezone(pytz.UTC)


def _ensure_aware_utc(dt: datetime) -> datetime:
    """Делаем datetime timezone-aware в UTC (на входе может быть naive/aware)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(pytz.UTC)


class QRCodeService:
    # ---------- GET (Plural) ----------
    @classmethod
    async def get_qr_codes(
        cls,
        *,
        qr_id: Optional[int] = None,
        user_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        valid_within_minutes: Optional[int] = None,   # фильтр «активен последние N минут»
        newest_first: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[QRCode]:
        async with AsyncSessionLocal() as session:
            stmt = select(QRCode)
            if qr_id is not None:
                stmt = stmt.where(QRCode.id == qr_id)
            if user_id is not None:
                stmt = stmt.where(QRCode.user_id == user_id)
            if phone_number is not None:
                stmt = stmt.where(QRCode.phone_number == phone_number)
            if newest_first:
                stmt = stmt.order_by(QRCode.created_at.desc())
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            rows = list(res.scalars().all())

            # Пост-фильтр по «валиден N минут» — надёжно даже если в БД naive timestamps
            if valid_within_minutes is not None:
                threshold = _now_utc() - timedelta(minutes=valid_within_minutes)
                filtered: List[QRCode] = []
                for qr in rows:
                    if not qr.created_at:
                        continue
                    created_at_utc = _ensure_aware_utc(qr.created_at)
                    if created_at_utc >= threshold:
                        filtered.append(qr)
                rows = filtered

            return rows

    # ---------- GET (single) ----------
    @classmethod
    async def get_qr_code(cls, **kwargs) -> Optional[QRCode]:
        rows = await QRCodeService.get_qr_codes(limit=1, **kwargs)
        return rows[0] if rows else None

    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        qr_id: Optional[int] = None,
        user_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        created_at: Optional[datetime] = None,
        update_latest_for_user: bool = False,
    ) -> QRCode:
        """
        Создаёт или обновляет QR-код.

        Варианты:
        - Передан qr_id → обновляем запись.
        - Не передан qr_id:
            - если update_latest_for_user=True и задан user_id — обновим последний QR пользователя (если он есть),
              иначе создадим новый;
            - по умолчанию — создадим новый (user_id и phone_number обязательны).
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[QRCode] = None

                # Найти обновляемую запись
                if qr_id is not None:
                    res = await session.execute(select(QRCode).where(QRCode.id == qr_id))
                    instance = res.scalars().first()
                    if instance is None:
                        raise ValueError("QRCode с таким id не найден")
                elif update_latest_for_user and user_id is not None:
                    res = await session.execute(
                        select(QRCode)
                        .where(QRCode.user_id == user_id)
                        .order_by(QRCode.created_at.desc())
                        .limit(1)
                    )
                    instance = res.scalars().first()

                # Создание
                if instance is None:
                    if user_id is None or phone_number is None:
                        raise ValueError("Для создания QR-кода требуются user_id и phone_number")
                    instance = QRCode(
                        user_id=user_id,
                        phone_number=phone_number,
                        created_at=_ensure_aware_utc(created_at) if created_at else _now_utc(),
                    )
                    session.add(instance)
                # Обновление
                else:
                    if user_id is not None:
                        instance.user_id = user_id
                    if phone_number is not None:
                        instance.phone_number = phone_number
                    if created_at is not None:
                        instance.created_at = _ensure_aware_utc(created_at)

            await session.refresh(instance)
            return instance
