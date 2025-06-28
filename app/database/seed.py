from sqlalchemy import select
from .models import ItemType, Category, async_session

ITEM_TYPES = ["Резина", "Диски"]
R_VALUES = [f"R{r}" for r in range(14, 23)]


async def seed():
    async with async_session() as session:
        for val in ITEM_TYPES:
            result = await session.execute(select(ItemType).where(ItemType.value == val))
            item_type = result.scalar_one_or_none()

            if not item_type:
                item_type = ItemType(value=val)
                session.add(item_type)
                await session.flush()

            result = await session.execute(
                select(Category.value).where(Category.type_id == item_type.id)
            )
            existing_categories = {row[0] for row in result.all()}

            for r in R_VALUES:
                if r not in existing_categories:
                    category = Category(value=r, type_id=item_type.id)
                    session.add(category)

        await session.commit()
        print("✅ Категории успешно добавлены или уже существовали.")