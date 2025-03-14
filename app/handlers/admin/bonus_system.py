from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from app.handlers.main import admin_router
import app.database.admin_requests as rq
import app.database.requests as common_rq
import app.keyboards.admin.admin as kb
from app.handlers.admin.admin import cmd_job


# Изменение кешбека и макс списания
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


# Меню взаимодействия с пользователями в бонусной системе
@admin_router.callback_query(F.data == 'interact_with_user_bonus')
async def interact_with_users_bonus(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "🎉 Вы перешли в раздел взаимодействия с бонусами пользователей! 🎉\n\n"
        "💡 Воспользуйтесь меню ниже для управления бонусами:",
        parse_mode='HTML',
        reply_markup=kb.users_balance
    )


@admin_router.callback_query(F.data.startswith("bonus_users:"))
async def employee_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, balance = callback.data.split(":")
    balance = float(balance)

    users_dict = await rq.get_users_by_balance(balance)

    await state.update_data(users_dict=users_dict)

    keyboard = await kb.create_users_keyboard(users_dict, page=1)

    await callback.message.edit_text(
        "<b>Отображаю список пользователей</b> 📋\n",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@admin_router.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    page = int(callback.data.split(":")[1])

    data = await state.get_data()
    users_dict = data.get("users_dict", {})

    keyboard = await kb.create_users_keyboard(users_dict, page=page)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@admin_router.callback_query(F.data.startswith("bonus_user:"))
async def view_user_profile(callback: CallbackQuery):
    await callback.answer()

    _, user_id = callback.data.split(":")

    profile_user_data = await common_rq.get_user_profile(user_id)

    registration_date = profile_user_data['registration_date'].replace("-", ".")
    birthday_date = profile_user_data['birthday_date'].replace("-", ".")

    keyboard = await kb.get_user_profile_admin(user_id)

    await callback.message.edit_text(
        f"<b>👤 Личный кабинет пользователя</b>\n"
        f"<b>——————</b>\n\n"
        f"<b>🆔 ID:</b> <code>{profile_user_data['user_id']}</code>\n\n"
        f"<b>👋 Имя:</b> {profile_user_data['name']}\n\n"
        f"<b>📅 Дата регистрации:</b> {registration_date}\n\n"
        f"<b>📞 Номер телефона:</b> {profile_user_data['mobile_phone']}\n\n"
        f"<b>🎂 Дата рождения:</b> {birthday_date}\n\n"
        f"<b>💰 Бонусный баланс:</b> {profile_user_data['bonus_balance']} бонусов\n\n",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@admin_router.callback_query(F.data.startswith("history_purchase_user:"))
async def history_purchase(callback: CallbackQuery):
    await callback.answer("")
    _, user_id = callback.data.split(":")

    transactions = await common_rq.get_last_10_transactions(user_id)

    if not transactions:
        await callback.message.answer("🛒 История покупок пользователя пуста")
        return

    history_message = "📊 <b>История последних 10 покупок/списаний:</b>\n\n"

    for transaction in transactions:
        transaction_date = transaction.transaction_date.strftime("%d.%m.%Y %H:%M")
        transaction_type = transaction.transaction_type
        amount = f"{transaction.amount:.2f} руб."

        bonus_text = (
            f"Получено бонусов: {transaction.bonus_amount}"
            if transaction_type == "Пополнение"
            else f"Списано бонусов: {transaction.bonus_amount}"
        )

        history_message += (
            f"📅 <b>Дата:</b> {transaction_date}\n"
            f"<b>Тип:</b> {transaction_type}\n"
            f"<b>Сумма:</b> {amount}\n"
            f"<b>{bonus_text}</b>\n"
            f"————————————\n"
        )

    await callback.message.answer(history_message, parse_mode="HTML", reply_markup=kb.delete_button_admin)


@admin_router.callback_query(F.data == "delete_button_admin")
async def delete_history_message(callback: CallbackQuery):
    await callback.answer()

    await callback.message.delete()


class GetAmount(StatesGroup):
    amount = State()

@admin_router.callback_query(F.data.startswith("bonus:"))
async def view_user_profile(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, action, user_id = callback.data.split(":")

    await state.update_data(user_id=user_id, action=action)

    text = "Введите сумму, на которую хотите "
    text += "увеличить бонусный баланс 📈" if action == 'add' else "уменьшить бонусный баланс 📉"

    await state.set_state(GetAmount.amount)

    await callback.message.answer(
        f"{text} \n👇",
        parse_mode="HTML"
    )


@admin_router.message(GetAmount.amount)
async def handle_amount_input(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        if user_input.lower()=='отмена':
            await state.clear()
            await message.answer("✅ Операция успешно отменена")

            await cmd_job(message)

            return

        amount = int(user_input)
        if amount <= 0:
            await message.answer(
                "⚠️ Некорректное значение!\n"
                "Введите <b>положительное число</b> или <b>напишите 'отмена' для отмены операции</b>",
                parse_mode="HTML"
            )

            return

        data = await state.get_data()
        user_id = data.get("user_id")
        action = data.get("action")
        await state.clear()

        success = await common_rq.set_bonus_balance(user_id, action, amount, 0, "Администратор")
        if success:
            text = "Сумма пользователя была "
            text += "увеличена 📈" if action == 'add' else "уменьшена 📉"

            await message.answer(
                text=f"{text}\n✅ Операция успешно выполнена!",
                parse_mode="HTML"
            )
            await cmd_job(message)

    except ValueError:
        await message.answer(
            "❌ Ошибка! Введите корректное целое число.",
            parse_mode="HTML"
        )



