from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any

from app.database.model import AsyncSessionLocal, Item


class ItemService:
    """Сервис для работы с товарами"""

    # ---------- GET (Plural) ----------
    @classmethod
    async def get_items(
        cls,
        *,
        item_id: Optional[int] = None,
        category_id: Optional[int] = None,
        value: Optional[str] = None,
        with_category: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Item]:
        async with AsyncSessionLocal() as session:
            stmt = select(Item)
            if with_category:
                stmt = stmt.options(selectinload(Item.category))
            if item_id is not None:
                stmt = stmt.where(Item.id == item_id)
            if category_id is not None:
                stmt = stmt.where(Item.category_id == category_id)
            if value is not None:
                stmt = stmt.where(Item.value == value)
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())


    # ---------- GET (single) ----------
    @classmethod
    async def get_item(cls, **kwargs) -> Optional[Item]:
        rows = await ItemService.get_items(limit=1, **kwargs)
        return rows[0] if rows else None


    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        item_id: Optional[int] = None,
        value: Optional[str] = None,
        category_id: Optional[int] = None,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> Item:
        """
        Обновляет/создаёт товар.
        - При создании требуются value и category_id.
        - При обновлении меняет только переданные поля.
        - meta_data при обновлении заменяется целиком, если передана.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[Item] = None
                if item_id is not None:
                    result = await session.execute(
                        select(Item).where(Item.id == item_id)
                    )
                    instance = result.scalars().first()
                    if instance is None:
                        raise ValueError("Item с таким id не найден")

                if instance is None:
                    if not value or category_id is None:
                        raise ValueError("Для создания Item требуются value и category_id")
                    instance = Item(
                        value=value,
                        category_id=category_id,
                        meta_data=meta_data or {},
                    )
                    session.add(instance)
                else:
                    if value is not None:
                        instance.value = value
                    if category_id is not None:
                        instance.category_id = category_id
                    if meta_data is not None:
                        instance.meta_data = meta_data

            await session.refresh(instance)
            return instance


    # ---------- DELETE ----------
    @classmethod
    async def delete(cls, item_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                res = await session.execute(delete(Item).where(Item.id == item_id))
                affected = getattr(res, "rowcount", None)
            return bool(affected and affected > 0)