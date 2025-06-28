from sqlalchemy import select, func,and_
from sqlalchemy.orm import selectinload
from typing import List
from .models import async_session, Category, Item

async def get_all_categories(type_id: int) -> List[Category]:
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.type_id==type_id))
        categories = result.scalars().all()

        return categories


async def get_all_categories_with_active_items(type_id: int) -> List[Category]:
    async with async_session() as session:
        stmt = (
            select(Category)
            .options(selectinload(Category.items))  # загрузить связанные айтемы
            .where(Category.type_id == type_id)
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()

        filtered_categories = []
        for category in categories:
            active_items = [item for item in category.items if item.meta_data.get("status") == "active"]
            if active_items:
                category.items = active_items
                filtered_categories.append(category)

        return filtered_categories

async def get_items_by_category(category_id: int, status: str) -> List[Item]:
    async with async_session() as session:
        stmt = select(Item).where(
            and_(
                Item.category_id == category_id,
                func.json_extract(Item.meta_data, '$.status') == status
            )
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

        return items

async def get_category_by_id(category_id: int) -> Category:
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()

        return category

async def create_item_from_employee(
    category_id: int,
    brand: str,
    description: str,
    price: int,
    photos: list[str],
    season: str = None
):
        meta_data = {
            "status": "active",
            "description": description,
            "price": price,
            "photos": photos
        }
        if season:
            meta_data["season"] = season

        async with async_session() as session:
            item = Item(
                category_id=category_id,
                value=brand,
                meta_data=meta_data
            )
            session.add(item)
            await session.commit()

async def get_item_by_id(item_id: int) -> Item:
    async with async_session() as session:
        query = await session.execute(select(Item).where(Item.id==item_id))
        return query.scalar_one_or_none()

async def update_item(item_id: int, value: str = None, meta_data: dict = None):
    async with async_session() as session:
        item = await session.get(Item, item_id)

        if value is not None:
            item.value = value
        if meta_data is not None:
            item.meta_data = meta_data

        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item