from sqlalchemy import select, func
from typing import List
from .models import async_session, Category, Item

async def get_all_categories(type_id: int) -> List[Category]:
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.type_id==type_id))
        categories = result.scalars().all()

        return categories

async def get_all_categories_with_items(type_id: int) -> List[Category]:
    async with async_session() as session:
        stmt = (
            select(Category)
            .join(Category.items)
            .where(Category.type_id == type_id)
            .group_by(Category.id)
            .having(func.count(Category.items) > 0)
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()

        return categories

async def get_items_by_category(category_id: int) -> List[Item]:
    async with async_session() as session:
        result = await session.execute(select(Item).where(Item.category_id == category_id))
        items = result.scalars().all()

        return items

async def get_category_by_id(category_id: int) -> Category:
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()

        return category