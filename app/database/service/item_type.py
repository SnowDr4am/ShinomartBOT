from sqlalchemy import select
from typing import Optional, List

from app.database.model import AsyncSessionLocal, ItemType


class ItemTypeService:
    # ---------- GET (Plural) ----------
    @classmethod
    async def get_item_types(
        cls,
        *,
        item_type_id: Optional[int] = None,
        value: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ItemType]:
        async with AsyncSessionLocal() as session:
            stmt = select(ItemType)
            if item_type_id is not None:
                stmt = stmt.where(ItemType.id == item_type_id)
            if value is not None:
                stmt = stmt.where(ItemType.value == value)
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())


    # ---------- GET (single) ----------
    @classmethod
    async def get_item_type(cls, **kwargs) -> Optional[ItemType]:
        rows = await ItemTypeService.get_item_types(limit=1, **kwargs)
        return rows[0] if rows else None


    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        item_type_id: Optional[int] = None,
        value: Optional[str] = None,
    ) -> ItemType:
        """
        Если передан item_type_id — обновляет существующую запись.
        Если нет — создаёт новую (value обязателен).
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[ItemType] = None
                if item_type_id is not None:
                    result = await session.execute(
                        select(ItemType).where(ItemType.id == item_type_id)
                    )
                    instance = result.scalars().first()
                    if instance is None:
                        raise ValueError("ItemType с таким id не найден")

                if instance is None:
                    if not value:
                        raise ValueError("Для создания ItemType требуется value")
                    instance = ItemType(value=value)
                    session.add(instance)
                else:
                    if value is not None:
                        instance.value = value

            await session.refresh(instance)
            return instance