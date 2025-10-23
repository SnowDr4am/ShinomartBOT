import os

from aiogram import F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime, date

from app.handlers.main import employee_router
from app.utils.states import StorageCellStates
import app.keyboards.employee.storage_cells.interaction_with_cell_data as kb
import app.database.StorageCellsService as storage_service
import app.database.requests as rq
from app.utils.word import generate_storage_word_document


# ==================== Управление заполненной ячейкой ====================


# ==================== Отправка WORD файла ====================

@employee_router.callback_query(F.data.startswith("storage_generate_word:"))
async def regenerate_word_document(callback: CallbackQuery):
    """Отправка последнего созданного Word-документа (если нет — генерация)"""
    await callback.answer()

    cell_id = int(callback.data.split(":")[-1])
    cell = await storage_service.get_cell(cell_id)

    if not cell or not cell.cell_storage:
        return await callback.answer("❌ Ячейка не найдена или пуста!", show_alert=True)

    cell_folder = os.path.join("static", "storage_cells", str(cell_id))
    latest_file_path = None
    if os.path.isdir(cell_folder):
        files = [
            os.path.join(cell_folder, f)
            for f in os.listdir(cell_folder)
            if
            os.path.isfile(os.path.join(cell_folder, f)) and (f.lower().endswith(".docx") or f.lower().endswith(".txt"))
        ]
        if files:
            latest_file_path = max(files, key=lambda p: os.path.getmtime(p))

    if latest_file_path and os.path.exists(latest_file_path):
        return await callback.message.answer_document(
            document=FSInputFile(latest_file_path),
            caption=f"📄 <b>Последний документ для ячейки №{cell_id}</b>",
            parse_mode="HTML",
            reply_markup=kb.delete_message_keyboard
        )

    storage = cell.cell_storage
    user_data = await rq.get_user_by_phone(storage.user_id)
    worker_data = await rq.get_user_by_id(user_id=storage.worker_id)
    word_file = await generate_storage_word_document(storage, user_data, worker_data)

    if word_file and os.path.exists(word_file):
        await callback.message.answer_document(
            document=FSInputFile(word_file),
            caption=f"📄 <b>Документ для ячейки №{cell_id}</b>\n(создан сейчас, т.к. ранее не было файлов)",
            parse_mode="HTML",
            reply_markup=kb.delete_message_keyboard
        )
    else:
        await callback.answer("❌ Не удалось найти или сгенерировать документ!", show_alert=True)


# ==================== Продление хранения ====================

@employee_router.callback_query(F.data.startswith("storage_extend:"))
async def extend_storage_period(callback: CallbackQuery, state: FSMContext):
    cell_id = int(callback.data.split(":")[1])
    await state.update_data(extend_cell_id=cell_id)

    cell = await storage_service.get_cell(cell_id)
    scheduled_month = getattr(getattr(cell, "cell_storage", None), "scheduled_month", None)

    if scheduled_month:
        current_year = scheduled_month.year
        selected_month = scheduled_month.month
        await state.update_data(
            current_year=current_year,
            selected_month=selected_month,
            selected_year=current_year
        )
    else:
        current_year = datetime.now().year
        selected_month = None
        await state.update_data(current_year=current_year, selected_month=None, selected_year=None)

    keyboard = await kb.generate_month_keyboard(current_year, cell_id, selected_month)

    await callback.message.edit_text(
        f"📅 <b>Продление срока хранения для ячейки №{cell_id}</b>\n\n"
        "Выберите новый месяц:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(StorageCellStates.waiting_extend_month)



@employee_router.callback_query(StorageCellStates.waiting_extend_month, F.data.startswith("storage_year:"))
async def extend_change_year(callback: CallbackQuery, state: FSMContext):
    year = int(callback.data.split(":")[1])
    await state.update_data(current_year=year)

    data = await state.get_data()
    cell_id = data.get("extend_cell_id")
    selected_month = data.get("selected_month")
    selected_year = data.get("selected_year")

    highlight_month = selected_month if selected_year == year else None

    keyboard = await kb.generate_month_keyboard(year, cell_id, highlight_month)

    await callback.message.edit_text(
        f"📅 <b>Продление срока хранения для ячейки №{cell_id}</b>\n\n"
        "Выберите новый месяц:",
        parse_mode="HTML",
        reply_markup=keyboard
    )



@employee_router.callback_query(StorageCellStates.waiting_extend_month, F.data.startswith("storage_month:"))
async def process_extend_month(callback: CallbackQuery, state: FSMContext):
    """Обработка нового месяца при продлении"""
    parts = callback.data.split(":")
    year = int(parts[1])
    month = int(parts[2])

    new_date = date(year, month, 1)

    data = await state.get_data()
    cell_id = data.get("extend_cell_id")

    await state.update_data(selected_month=month, current_year=year)

    success = await storage_service.update_scheduled_month(cell_id, new_date)

    if success:
        await callback.message.edit_text(
            f"✅ <b>Срок хранения продлён!</b>\n\n"
            f"Новый срок: <b>{format_month_ru(new_date)}</b>",
            parse_mode="HTML",
            reply_markup=kb.generate_simple_keyboard("Назад", f"storage_cell:{cell_id}")
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось продлить срок хранения!",
            parse_mode="HTML",
            reply_markup=kb.generate_simple_keyboard("Назад", f"storage_cell:{cell_id}")
        )

    await state.clear()


# ==================== Освобождение ячейки ====================

@employee_router.callback_query(F.data.startswith("storage_free:"))
async def free_storage_cell(callback: CallbackQuery):
    """Освобождение ячейки"""
    await callback.answer()

    cell_id = int(callback.data.split(":")[1])
    keyboard = await kb.get_confirmation_keyboard("free", cell_id)

    await callback.message.edit_text(
        f"🔓 <b>Освобождение ячейки №{cell_id}</b>\n\n"
        "⚠️ Вы уверены, что хотите очистить ячейку?\n"
        "Все данные о хранении будут удалены.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ==================== Удаление ячейки ====================

@employee_router.callback_query(F.data.startswith("storage_delete:"))
async def delete_storage_cell(callback: CallbackQuery):
    """Удаление ячейки"""
    await callback.answer()

    cell_id = int(callback.data.split(":")[1])
    keyboard = await kb.get_confirmation_keyboard("delete", cell_id)

    await callback.message.edit_text(
        f"🗑️ <b>Удаление ячейки №{cell_id}</b>\n\n"
        "⚠️ Вы уверены, что хотите ПОЛНОСТЬЮ удалить ячейку?\n"
        "Это действие нельзя отменить!",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@employee_router.callback_query(F.data.startswith("storage_confirm:"))
async def confirm_action(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]
    cell_id = int(parts[2])

    if action == "delete":
        # Удаляем ячейку полностью
        success = await storage_service.delete_storage_cell(cell_id)
        if success:
            await callback.message.edit_text(
                f"✅ <b>Ячейка №{cell_id} удалена!</b>",
                parse_mode="HTML",
                reply_markup=kb.generate_simple_keyboard("Назад", "storage_open_cells")
            )
        else:
            await callback.message.edit_text(
                "❌ Не удалось удалить ячейку!",
                parse_mode="HTML",
                reply_markup=kb.generate_simple_keyboard("Назад", "storage_open_cells")
            )


RU_MONTHS_NOM = [
    "Январь", "Февраль", "Март",
    "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь",
    "Октябрь", "Ноябрь", "Декабрь"
]

def format_month_ru(dt) -> str:
    return f"{RU_MONTHS_NOM[dt.month - 1]} {dt.year}"