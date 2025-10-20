from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.database.model import AsyncSessionLocal, Category


class CategoryService:
    """Сервис для работы с категориями"""
    # ---------- GET (Plural) ----------
    @classmethod
    async def get_categories(
        cls,
        *,
        category_id: Optional[int] = None,
        type_id: Optional[int] = None,
        value: Optional[str] = None,
        with_type: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Category]:
        async with AsyncSessionLocal() as session:
            stmt = select(Category)
            if with_type:
                stmt = stmt.options(selectinload(Category.item_type))
            if category_id is not None:
                stmt = stmt.where(Category.id == category_id)
            if type_id is not None:
                stmt = stmt.where(Category.type_id == type_id)
            if value is not None:
                stmt = stmt.where(Category.value == value)
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())


    # ---------- GET (single) ----------
    @classmethod
    async def get_category(cls, **kwargs) -> Optional[Category]:
        rows = await CategoryService.get_categories(limit=1, **kwargs)
        return rows[0] if rows else None


    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        category_id: Optional[int] = None,
        value: Optional[str] = None,
        type_id: Optional[int] = None,
    ) -> Category:
        """
        Обновляет/создаёт категорию.
        - При создании требуются value и type_id.
        - При обновлении меняет только переданные поля.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[Category] = None
                if category_id is not None:
                    result = await session.execute(
                        select(Category).where(Category.id == category_id)
                    )
                    instance = result.scalars().first()
                    if instance is None:
                        raise ValueError("Category с таким id не найдена")

                if instance is None:
                    if not value or type_id is None:
                        raise ValueError("Для создания Category требуются value и type_id")
                    instance = Category(value=value, type_id=type_id)
                    session.add(instance)
                else:
                    if value is not None:
                        instance.value = value
                    if type_id is not None:
                        instance.type_id = type_id

            await session.refresh(instance)
            return instance