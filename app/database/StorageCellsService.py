import shutil, asyncio
from pathlib import Path
from datetime import date
from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from .models import async_session, StorageCell, CellStorage


async def get_cells() -> List[StorageCell]:
    """Получение всех ячеек с их содержимым"""
    async with async_session() as session:
        stmt = (
            select(StorageCell)
            .options(selectinload(StorageCell.cell_storage))
            .order_by(StorageCell.value, StorageCell.id)
        )
        result = await session.execute(stmt)
        cells = result.scalars().all()
        return list(cells)


async def get_cell(cell_id: int) -> Optional[StorageCell]:
    """Получение конкретной ячейки"""
    async with async_session() as session:
        stmt = (
            select(StorageCell)
            .options(selectinload(StorageCell.cell_storage))
            .where(StorageCell.id == cell_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def create_cells(count: int) -> List[StorageCell]:
    """Создание новых ячеек с заполнением пропусков в value."""
    async with async_session() as session:
        # Получаем существующие значения value
        stmt_existing = select(StorageCell.value).order_by(StorageCell.value)
        result = await session.execute(stmt_existing)
        existing_values = [v for (v,) in result.all() if v is not None]

        # Вычисляем пропуски начиная с 1
        missing_values = []
        expected = 1
        for val in existing_values:
            while expected < val and len(missing_values) < count:
                missing_values.append(expected)
                expected += 1
            expected = val + 1

        # Если ещё нужно, продолжаем после максимума
        while len(missing_values) < count:
            missing_values.append(expected)
            expected += 1

        new_cells: List[StorageCell] = []
        for i in range(count):
            cell = StorageCell(value=missing_values[i])
            session.add(cell)
            new_cells.append(cell)

        await session.commit()

        for cell in new_cells:
            await session.refresh(cell)

        return new_cells


async def save_or_update_cell_storage(
    cell_id: int,
    worker_id: int,
    user_id: int,
    storage_type: str,
    price: float,
    description: str,
    scheduled_month: date,
    meta_data: dict,
    action_type: str = "handover",  # handover (сдача) или pickup (получение)
    confirmation_status: str = "pending"
) -> CellStorage:
    """Обновляет или создает запись в cell_storages"""
    async with async_session() as session:
        # Проверяем, есть ли уже запись для этой ячейки
        stmt = select(CellStorage).where(CellStorage.cell_id == cell_id)
        result = await session.execute(stmt)
        cell_storage = result.scalar_one_or_none()
        
        if cell_storage:
            # Обновляем существующую запись
            cell_storage.worker_id = worker_id
            cell_storage.user_id = user_id
            cell_storage.storage_type = storage_type
            cell_storage.price = price
            cell_storage.description = description
            cell_storage.scheduled_month = scheduled_month
            cell_storage.meta_data = meta_data
            cell_storage.action_type = action_type
            cell_storage.confirmation_status = confirmation_status
        else:
            # Создаем новую запись
            cell_storage = CellStorage(
                cell_id=cell_id,
                worker_id=worker_id,
                user_id=user_id,
                storage_type=storage_type,
                price=price,
                description=description,
                scheduled_month=scheduled_month,
                meta_data=meta_data,
                action_type=action_type,
                confirmation_status=confirmation_status
            )
            session.add(cell_storage)
        
        await session.commit()
        await session.refresh(cell_storage)
        return cell_storage


async def delete_cell_storage(cell_id: int) -> bool:
    """Удаляет запись из cell_storages"""
    async with async_session() as session:
        stmt = delete(CellStorage).where(CellStorage.cell_id == cell_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0


async def delete_storage_cell(cell_id: int) -> bool:
    """Удаляет ячейку и её папку."""
    async with async_session() as session:
        await session.execute(delete(CellStorage).where(CellStorage.cell_id == cell_id))
        result = await session.execute(delete(StorageCell).where(StorageCell.id == cell_id))
        await session.commit()

    folder = Path("static/storage_cells") / str(cell_id)
    if folder.is_dir():
        try:
            await asyncio.to_thread(shutil.rmtree, folder)
        except Exception as e:
            print(f"⚠️ Ошибка при удалении {folder}: {e}")

    return (getattr(result, "rowcount", 0) or 0) > 0

async def update_scheduled_month(cell_id: int, new_month: date) -> bool:
    """Обновляет срок хранения"""
    async with async_session() as session:
        stmt = select(CellStorage).where(CellStorage.cell_id == cell_id)
        result = await session.execute(stmt)
        cell_storage = result.scalar_one_or_none()
        
        if cell_storage:
            cell_storage.scheduled_month = new_month
            await session.commit()
            return True
        return False


async def update_confirmation_status(cell_storage_id: int, status: str) -> bool:
    """Обновляет статус подтверждения"""
    async with async_session() as session:
        stmt = select(CellStorage).where(CellStorage.id == cell_storage_id)
        result = await session.execute(stmt)
        cell_storage = result.scalar_one_or_none()
        
        if cell_storage:
            cell_storage.confirmation_status = status
            await session.commit()
            return True
        return False


async def get_cell_storage_by_id(cell_storage_id: int) -> Optional[CellStorage]:
    """Получает запись хранения по ID"""
    async with async_session() as session:
        stmt = select(CellStorage).where(CellStorage.id == cell_storage_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

