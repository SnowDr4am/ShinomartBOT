from aiogram import F
from aiogram.types import Message, CallbackQuery
from app.handlers.main import admin_router
import app.database.admin_requests as rq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class Personal(StatesGroup):
    role = State()
    action = State()
    waiting_for_user_id = State()

@admin_router.callback_query(F.data.startswith('action:'))
async def change_setting(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    role, action = callback.data.split(':')[1], callback.data.split(':')[2]

    if action == "remove":
        if role == '728303180':
            await callback.message.answer("Любые взаимодействия с этим пользователем запрещены")
            return

        success = await rq.change_user_role(role, "Пользователь")
        if success:
            await callback.message.answer(f"Пользователь {role} успешно снят с должности")
            await state.clear()
            await rq.add_role_history(callback.message.from_user.id, role, "Пользователь")
            return
        else:
            await callback.message.answer(f"Пользователь {role} не найден в базе. \nПроверьте его ID")
            return

    await state.update_data(action=action, role=role)

    await callback.message.answer("Введите ID пользователя:")
    await state.set_state(Personal.waiting_for_user_id)


@admin_router.message(Personal.waiting_for_user_id)
async def handle_user_id_input(message: Message, state: FSMContext):
    user_input = message.text.strip()

    data = await state.get_data()
    role = data.get("role")

    if role == "admin":
        role = "Администратор"
    else:
        role = "Работник"

    success = await rq.change_user_role(user_input, role)
    if success:
        await message.answer(f"Пользователь {user_input} успешно получил роль {role}")
        await state.clear()
        await rq.add_role_history(message.from_user.id, user_input, role)
    else:
        await message.answer(f"Пользователь {user_input} не найден в базе. \nПроверьте его ID")
        return