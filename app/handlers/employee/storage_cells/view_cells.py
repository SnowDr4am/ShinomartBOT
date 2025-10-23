from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.handlers.main import employee_router
import app.keyboards.employee.storage_cells.view_cells as kb
import app.keyboards.employee.storage_cells.menu as menu_kb
import app.database.StorageCellsService as storage_service
import app.database.requests as rq


# ==================== Просмотр списка ячеек ====================

@employee_router.callback_query(F.data == "storage_open_cells")
async def storage_open_cells(callback: CallbackQuery, state: FSMContext):
    """Открытие списка ячеек"""
    await callback.answer()
    
    cells = await storage_service.get_cells()
    
    if not cells:
        await callback.message.edit_text(
            "📦 <b>Ячейки отсутствуют</b>\n\n"
            "Сначала необходимо добавить ячейки.",
            parse_mode="HTML",
            reply_markup=menu_kb.storage_main_menu
        )
        return

    await state.update_data(current_page=1)
    
    await callback.message.edit_text(
        f"📦 <b>Ячейки хранения</b>\n\n"
        f"Всего ячеек: {len(cells)}\n"
        f"✅ - занятая ячейка\n\n"
        f"Выберите ячейку:",
        parse_mode="HTML",
        reply_markup=kb.generate_cells_keyboard(cells, page=1)
    )


@employee_router.callback_query(F.data.startswith("storage_page:"))
async def storage_page_navigation(callback: CallbackQuery, state: FSMContext):
    """Навигация по страницам ячеек"""
    await callback.answer()
    
    page = int(callback.data.split(":")[1])
    cells = await storage_service.get_cells()

    await state.update_data(current_page=page)
    
    await callback.message.edit_text(
        f"📦 <b>Ячейки хранения</b>\n\n"
        f"Всего ячеек: {len(cells)}\n"
        f"✅ - занятая ячейка\n\n"
        f"Выберите ячейку:",
        parse_mode="HTML",
        reply_markup=kb.generate_cells_keyboard(cells, page=page)
    )

# ==================== Просмотр информации о конкретной ячейке ====================

@employee_router.callback_query(F.data.startswith("storage_cell:"))
async def storage_cell_info(callback: CallbackQuery):
    """Отображение информации о ячейке"""
    cell_id = int(callback.data.split(":")[1])
    cell = await storage_service.get_cell(cell_id)
    
    if not cell:
        return await callback.answer("❌ Ячейка не найдена!", show_alert=True)
    
    # Проверяем, занята ли ячейка
    if cell.cell_storage:
        storage = cell.cell_storage
        # Клиент
        user_data = await rq.get_user_by_id(storage.user_id)
        user_name = f'<a href="tg://user?id={user_data.user_id}">{user_data.name}</a>'
        user_phone = user_data.mobile_phone

        # Сотрудник
        worker_data = await rq.get_user_by_id(storage.worker_id)
        worker_name = f'<a href="tg://user?id={worker_data.user_id}">{worker_data.name}</a>'
        worker_phone = worker_data.mobile_phone

        # Даты и суммы
        created_date = storage.created_at.strftime("%d.%m.%Y")
        months_ru = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь",
                     "Ноябрь", "Декабрь"]
        scheduled_date = f"{months_ru[storage.scheduled_month.month - 1]} {storage.scheduled_month.year}"
        price_str = f"{int(storage.price):,}".replace(",", " ")

        # Тип хранения → человекочитаемо
        st = str(storage.storage_type).lower()
        human_type = "Шины с дисками" if ("rim" in st or "диск" in st or "with" in st) else "Шины"

        text = (
            f"📦 <b>Ячейка №{cell.id}</b>\n"
            f"<b>Статус:</b> ✅ Занята\n"
            f"———————————————\n"
            f"👤 <b>Клиент</b>\n"
            f"• Имя: {user_name}\n"
            f"• Телефон: {user_phone}\n\n"
            f"🧑‍🔧 <b>Сотрудник</b>\n"
            f"• Имя: {worker_name}\n"
            f"• Телефон: {worker_phone}\n\n"
            f"🛞 <b>Хранение</b>\n"
            f"• Тип: {human_type}\n"
            f"• Описание: {storage.description or 'Отсутствует'}\n"
            f"• Цена: {price_str} ₽\n"
            f"• Размещено: {created_date}\n"
            f"• До: {scheduled_date}"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=kb.get_filled_cell_keyboard(cell_id)
        )
        
    else:
        await callback.message.edit_text(
            f"📦 <b>Ячейка №{cell.id}</b>\n\n"
            f"<b>Статус:</b> 🔓 Свободна\n\n"
            "Эта ячейка пуста. Используйте соответствующую команду для заполнения.",
            parse_mode="HTML",
            reply_markup=kb.build_empty_cell(cell_id)
        )
