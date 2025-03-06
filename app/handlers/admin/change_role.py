from aiogram import F
from aiogram.types import Message, CallbackQuery
from app.handlers.main import admin_router
import app.database.admin_requests as rq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.handlers.admin.admin import back_to_main, cmd_job


class Personal(StatesGroup):
    role = State()
    action = State()
    waiting_for_user_id = State()

@admin_router.callback_query(F.data.startswith('action:'))
async def change_setting(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, role, action = callback.data.split(":")

    if action == "remove":
        if role == '728303180':
            await callback.message.answer(
                "🚫 Действие запрещено!\n"
                "Вы не можете взаимодействовать с этим пользователем."
            )
            return

        success = await rq.change_user_role(role, "Пользователь")
        if success:
            await callback.message.answer(
                f"✅ Пользователь <b>{role}</b> успешно снят с должности.",
                parse_mode="HTML"
            )
            await state.clear()
            await rq.add_role_history(callback.message.from_user.id, role, "Пользователь")

            await back_to_main(callback)
            return
        else:
            await callback.message.answer(
                f"⚠️ Пользователь <b>{role}</b> не найден в базе.\n"
                "Пожалуйста, проверьте его ID.",
                parse_mode="HTML"
            )
            return

    await state.update_data(action=action, role=role)

    await callback.message.answer("✏️ Введите ID пользователя:")
    await state.set_state(Personal.waiting_for_user_id)


@admin_router.message(Personal.waiting_for_user_id)
async def handle_user_id_input(message: Message, state: FSMContext):
    user_input = message.text.strip()

    data = await state.get_data()
    role = "Администратор" if data.get("role") == "admin" else "Работник"

    success = await rq.change_user_role(user_input, role)
    if success:
        await message.answer(
            f"✅ Пользователь <b>{user_input}</b> успешно получил роль <b>{role}</b>.",
            parse_mode="HTML"
        )
        await state.clear()
        await rq.add_role_history(message.from_user.id, user_input, role)

        await cmd_job(message)
    else:
        await message.answer(
            f"⚠️ Пользователь <b>{user_input}</b> не найден в базе.\n"
            "Пожалуйста, проверьте его ID.",
            parse_mode="HTML"
        )
        return