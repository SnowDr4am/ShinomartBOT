from __future__ import annotations

from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete
from app.database.model import AsyncSessionLocal, Promotion


class PromotionService:
    # ---------- GET (Plural) ----------
    @classmethod
    async def get_promotions(
        cls,
        *,
        promo_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Promotion]:
        async with AsyncSessionLocal() as session:
            stmt = select(Promotion)
            if promo_id is not None:
                stmt = stmt.where(Promotion.id == promo_id)
            if is_active is not None:
                stmt = stmt.where(Promotion.is_active == is_active)
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())


    # ---------- GET (single) ----------
    @classmethod
    async def get_promotion(cls, **kwargs) -> Optional[Promotion]:
        rows = await PromotionService.get_promotions(limit=1, **kwargs)
        return rows[0] if rows else None


    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        promo_id: Optional[int] = None,
        short_description: Optional[str] = None,
        full_description: Optional[str] = None,
        image_path: Optional[str] = None,
        is_active: Optional[bool] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Promotion:
        """
        Если передан promo_id — обновляет запись.
        Если нет — создаёт новую. Для создания нужен хотя бы short_description.
        Допускается алиас data['full_text'] -> full_description (совместимость).
        """
        # Разбор data, если передано
        if data:
            short_description = data.get("short_description", short_description)
            image_path = data.get("image_path", image_path)
            is_active = data.get("is_active", is_active)
            # поддержка старого ключа
            full_description = (
                data.get("full_description", data.get("full_text", full_description))
            )

        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[Promotion] = None

                if promo_id is not None:
                    res = await session.execute(
                        select(Promotion).where(Promotion.id == promo_id)
                    )
                    instance = res.scalars().first()
                    if instance is None:
                        raise ValueError("Promotion с таким id не найдена")

                # Создание
                if instance is None:
                    if not short_description:
                        raise ValueError(
                            "Для создания Promotion требуется short_description"
                        )
                    instance = Promotion(
                        short_description=short_description,
                        full_description=full_description,
                        image_path=image_path,
                        is_active=is_active if is_active is not None else True,
                    )
                    session.add(instance)
                # Обновление
                else:
                    if short_description is not None:
                        instance.short_description = short_description
                    if full_description is not None:
                        instance.full_description = full_description
                    if image_path is not None:
                        instance.image_path = image_path
                    if is_active is not None:
                        instance.is_active = is_active

            await session.refresh(instance)
            return instance

    # ---------- DELETE ----------
    @classmethod
    async def delete(cls, promo_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                res = await session.execute(
                    delete(Promotion).where(Promotion.id == promo_id)
                )
                affected = getattr(res, "rowcount", None)
            return bool(affected and affected > 0)