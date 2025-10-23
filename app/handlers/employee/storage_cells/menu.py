from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.handlers.main import employee_router
import app.keyboards.employee.storage_cells.menu as kb


@employee_router.message(F.text == '📦 Хранение шин')
async def storage_menu_handler(message: Message, state: FSMContext):
    """Обработчик кнопки 'Хранение шин'"""
    await message.delete()
    await state.clear()

    await message.answer(
        "📦 <b>Хранение шин</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=kb.storage_main_menu
    )


@employee_router.callback_query(F.data == "storage_menu")
async def storage_menu(callback: CallbackQuery, state: FSMContext):
    """Главное меню хранения шин"""
    await state.clear()

    await callback.message.edit_text(
        "📦 <b>Хранение шин</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=kb.storage_main_menu
    )