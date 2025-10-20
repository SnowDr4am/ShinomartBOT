#!/usr/bin/env python3
"""
Скрипт для заполнения начальных данных в PostgreSQL базе данных
"""
import asyncio
from sqlalchemy import select

from app.database.model.database import AsyncSessionLocal
from app.database.model.item_type import ItemType
from app.database.model.categories import Category


ITEM_TYPES = ["Резина", "Диски"]
R_VALUES = [f"R{r}" for r in range(13, 23)]


async def seed_initial_data():
    """Заполнение начальных данных"""
    print("🔄 Заполнение начальных данных...")
    
    async with AsyncSessionLocal() as session:
        # Заполняем типы товаров и категории
        for val in ITEM_TYPES:
            # Проверяем, существует ли тип товара
            result = await session.execute(select(ItemType).where(ItemType.value == val))
            item_type = result.scalar_one_or_none()

            if not item_type:
                item_type = ItemType(value=val)
                session.add(item_type)
                await session.flush()
                print(f"✅ Создан тип товара: {val}")

            # Проверяем существующие категории для этого типа
            result = await session.execute(
                select(Category.value).where(Category.type_id == item_type.id)
            )
            existing_categories = {row[0] for row in result.all()}

            # Создаем категории
            for r in R_VALUES:
                if r not in existing_categories:
                    category = Category(value=r, type_id=item_type.id)
                    session.add(category)
                    print(f"✅ Создана категория: {r} для типа {val}")

        await session.commit()
        print("\n🎉 Начальные данные заполнены успешно!")


async def main():
    """Основная функция"""
    await seed_initial_data()


if __name__ == "__main__":
    asyncio.run(main())


