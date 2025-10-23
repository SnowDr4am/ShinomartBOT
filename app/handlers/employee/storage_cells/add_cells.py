from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.handlers.main import employee_router
from app.utils.states import StorageCellStates
import app.keyboards.employee.storage_cells.add_cells as kb
import app.database.StorageCellsService as storage_service
from app.utils.func import update_message_ids_in_state, delete_message_in_state


# ==================== Добавление ячеек ====================

@employee_router.callback_query(F.data == "storage_add_cells")
async def storage_add_cells(callback: CallbackQuery, state: FSMContext):
    """Запрос количества ячеек для добавления"""
    await callback.answer()
    sent = await callback.message.edit_text(
        "➕ <b>Добавление новых ячеек</b>\n\n"
        "Введите количество ячеек, которые необходимо добавить:\n\n"
        "<i>Для отмены напишите 'отмена'</i>",
        parse_mode="HTML",
        reply_markup=kb.generate_simple_keyboard("Назад", "storage_menu")
    )
    await state.set_state(StorageCellStates.waiting_cell_count)
    await update_message_ids_in_state(state, "action_message_ids", sent.message_id)


@employee_router.message(StorageCellStates.waiting_cell_count)
async def process_cell_count(message: Message, state: FSMContext):
    """Обработка количества ячеек и их создание"""
    await update_message_ids_in_state(state, "action_message_ids", message.message_id)

    try:
        count = int(message.text.strip())
        if count <= 0:
            sent = await message.answer("⚠️ Количество должно быть положительным числом!")
            return await update_message_ids_in_state(state, "action_message_ids", sent.message_id)

        if count > 1000:
            sent = await message.answer("⚠️ Максимальное количество ячеек за раз - 1000!")
            return await update_message_ids_in_state(state, "action_message_ids", sent.message_id)

        # Создаём ячейки
        new_cells = await storage_service.create_cells(count)

        await delete_message_in_state(message.bot, state, message.from_user.id)
        await state.clear()
        await message.answer(
            f"✅ <b>Успешно создано ячеек: {len(new_cells)}</b>",
            parse_mode="HTML",
            reply_markup=kb.generate_simple_keyboard("Назад", "storage_menu")
        )
    except ValueError:
        sent = await message.answer(
            "❌ Пожалуйста, введите корректное число!",
            parse_mode="HTML"
        )
        await update_message_ids_in_state(state, "action_message_ids", sent.message_id)