from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from app.handlers.main import admin_router
import app.database.admin_requests as rq


class BonusSystemState(StatesGroup):
    setting_type = State()
    amount = State()


@admin_router.callback_query(F.data.startswith('change:'))
async def change_setting(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    setting_type = callback.data.split(':')[1]

    await state.update_data(setting_type=setting_type)
    await state.set_state(BonusSystemState.amount)
    await callback.message.answer(f"Введите новое значение для {setting_type} (в процентах):")


@admin_router.message(BonusSystemState.amount)
async def handle_amount_input(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        amount = int(user_input)
        if not (0 <= amount <= 100):
            await message.answer("Вы ввели некорректное значение.\n Введите значение от 0 до 100")

            return

        data = await state.get_data()
        setting_type = data.get("setting_type")

        await rq.set_bonus_system_settings(amount, setting_type)
        await message.answer(f"Значение {setting_type} успешно изменено на {amount}%")
        await state.clear()
    except ValueError:
        await message.answer("Введите корректное целое число")