from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from app.handlers.main import admin_router
import app.database.admin_requests as rq
from app.handlers.admin.admin import cmd_job


class BonusSystemState(StatesGroup):
    setting_type = State()
    amount = State()


@admin_router.callback_query(F.data.startswith('change:'))
async def change_setting(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    setting_type = callback.data.split(':')[1]

    await state.update_data(setting_type=setting_type)
    await state.set_state(BonusSystemState.amount)
    await callback.message.answer(
        f"✏️ Введите новое значение для <b>{setting_type}</b> (в процентах):",
        parse_mode="HTML"
    )


@admin_router.message(BonusSystemState.amount)
async def handle_amount_input(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        amount = int(user_input)
        if not (0 <= amount <= 100):
            await message.answer(
                "⚠️ Некорректное значение!\n"
                "Введите число в диапазоне от <b>0</b> до <b>100</b>.",
                parse_mode="HTML"
            )

            return

        data = await state.get_data()
        setting_type = data.get("setting_type")

        await rq.set_bonus_system_settings(amount, setting_type)
        await message.answer(
            f"✅ Значение <b>{setting_type}</b> успешно обновлено до <b>{amount}%</b>!",
            parse_mode="HTML"
        )
        await state.clear()

        await cmd_job(message)
    except ValueError:
        await message.answer(
            "❌ Ошибка! Введите корректное целое число.",
            parse_mode="HTML"
        )