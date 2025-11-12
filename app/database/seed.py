from sqlalchemy import select, text
from .models import ItemType, Category, CellStorage, async_session


async def ensure_cell_storage_confirmation_fields() -> None:
    """Проверяет наличие полей confirmation_status и action_type у cell_storages и добавляет при отсутствии."""
    async with async_session() as session:
        # Проверяем существование колонок через PRAGMA table_info
        result = await session.execute(text("PRAGMA table_info(cell_storages)"))
        columns = result.fetchall()
        has_confirmation_status = any((col[1] == "confirmation_status") for col in columns)
        has_action_type = any((col[1] == "action_type") for col in columns)

        if not has_confirmation_status:
            # Добавляем колонку confirmation_status
            await session.execute(text("ALTER TABLE cell_storages ADD COLUMN confirmation_status VARCHAR DEFAULT 'confirmed'"))
            # Обновляем существующие записи
            await session.execute(text("UPDATE cell_storages SET confirmation_status = 'confirmed' WHERE confirmation_status IS NULL"))
            await session.commit()

        if not has_action_type:
            # Добавляем колонку action_type
            await session.execute(text("ALTER TABLE cell_storages ADD COLUMN action_type VARCHAR"))
            await session.commit()

ITEM_TYPES = ["Резина", "Диски"]
R_VALUES = [f"R{r}" for r in range(13, 23)]


async def seed():
    # Проверяем и добавляем поля подтверждения для cell_storages
    await ensure_cell_storage_confirmation_fields()
    
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