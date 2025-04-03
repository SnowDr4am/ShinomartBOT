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
    users_id = State()
    setting_type = State()
    amount = State()
    giftAmount = State()


@admin_router.callback_query(F.data.startswith('change:'))
async def change_setting(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    setting_type = callback.data.split(':')[1]

    await state.update_data(setting_type=setting_type)
    await state.set_state(BonusSystemState.amount)
    text = f"✏️ Введите новое значение для <b>{setting_type}</b>"
    if setting_type != "welcome_bonus":
        text += " (в процентах)"
    await callback.message.answer(
        text=text,
        parse_mode="HTML"
    )


@admin_router.message(BonusSystemState.amount)
async def handle_amount_input(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        amount = int(user_input)

        data = await state.get_data()
        setting_type = data.get("setting_type")

        report_text = f"✅ Значение <b>{setting_type} успешно обновлено</b> до {amount}"

        if setting_type != "welcome_bonus":
            report_text += "%"
            if not (0 <= amount <= 100):
                await message.answer(
                    "⚠️ Некорректное значение!\n"
                    "Введите число в диапазоне от <b>0</b> до <b>100</b>.",
                    parse_mode="HTML"
                )

                return

        await rq.set_bonus_system_settings(amount, setting_type)
        await message.answer(
            text=report_text,
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

    keyboard = await kb.get_user_profile_admin(user_id)

    await callback.message.edit_text(
        f"<b>👤 Личный кабинет пользователя</b>\n"
        f"<b>——————</b>\n\n"
        f"<b>🆔 ID:</b> <code>{profile_user_data['user_id']}</code>\n\n"
        f"<b>👋 Имя:</b> {profile_user_data['name']}\n\n"
        f"<b>📅 Дата регистрации:</b> {registration_date}\n\n"
        f"<b>📞 Номер телефона:</b> {profile_user_data['mobile_phone']}\n\n"
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


@admin_router.callback_query(F.data == 'presentBonus')
async def present_bonus(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.answer(
        "🎁 <b>Начисление бонусов</b>\n\n"
        "Введите номер телефона пользователя (формат: 89998887766) "
        "или напишите <code>all</code> для начисления всем:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode='HTML',
        reply_markup=kb.cancel_bonus_system
    )
    await state.set_state(BonusSystemState.users_id)

@admin_router.message(BonusSystemState.users_id)
async def process_give_bonus_user_id(message: Message, state: FSMContext):
    try:
        user_input = message.text.strip().lower()
        if user_input == "all":
            users = await rq.get_tg_id_users()

            await state.update_data(users_id=users)
            await message.answer(
                f"🔢 Бонусы будут начислены <b>{len(users)}</b> пользователям\n"
                "Введите сумму бонусов:",
                parse_mode='HTML',
                reply_markup=kb.cancel_bonus_system
            )
            await state.set_state(BonusSystemState.giftAmount)
        else:
            if not user_input.isdigit() or len(user_input) != 11:
                return await message.answer(
                    "❌ Неверный формат номера. Пример: <code>89998887766</code>",
                    parse_mode='HTML'
                )

            user = await common_rq.get_user_by_phone(user_input)
            if not user:
                return await message.answer(
                    f"❌ Пользователь с номером {user_input} не найден",
                    reply_markup=kb.cancel_bonus_system
                )

            await state.update_data(users_id=[user])
            await message.answer(
                f"👤 Бонусы будут начислены пользователю:\n"
                f"<code>{user_input}</code>\n\n"
                "Введите сумму бонусов:",
                parse_mode='HTML',
                reply_markup=kb.cancel_bonus_system
            )
            await state.set_state(BonusSystemState.giftAmount)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()
        await cmd_job(message)


@admin_router.message(BonusSystemState.giftAmount)
async def process_gift(message: Message, state: FSMContext):
    try:
        amount = message.text.strip()

        if not amount.isdigit() or int(amount) <= 0:
            return await message.answer(
                "❌ Введите целое положительное число",
                reply_markup=kb.delete_button_admin
            )

        amount = int(amount)
        data = await state.get_data()
        users = data["users_id"]

        success_count = 0
        failed_users = []

        for user_id in users:
            try:
                result = await common_rq.set_bonus_balance(user_id, "add", amount, 0, "Администратор")
                if result:
                    try:
                        await message.bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"🎁 <b>Вам начислен бонус!</b>\n\n"
                                f"▫️ Сумма: <b>{amount}</b> бонусов\n"
                                f"▫️ Причина: Подарок от администратора\n\n"
                            ),
                            parse_mode='HTML'
                        )
                        success_count += 1
                    except Exception as notify_error:
                        failed_users.append(f"{user_id} (ошибка уведомления: {str(notify_error)})")

                else:
                    failed_users.append(str(user_id))

            except Exception as e:
                failed_users.append(f"{user_id} (ошибка: {str(e)})")

        report = (
            f"📊 <b>Результат начисления бонусов</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Всего пользователей: <b>{len(users)}</b>\n"
            f"• Успешно: <b>{success_count}</b>\n"
        )

        if failed_users:
            report += (
                    f"\n❌ <b>Ошибки ({len(failed_users)}):</b>\n"
                    + "\n".join(f"▫️ {user}" for user in failed_users[:5])
            )
            if len(failed_users) > 5:
                report += f"\n... и ещё {len(failed_users) - 5} ошибок"

        await message.answer(
            report,
            parse_mode='HTML',
            reply_markup=kb.delete_button_admin
        )

    except Exception as e:
        await message.answer(
            f"❌ <b>Критическая ошибка:</b>\n{str(e)}",
            parse_mode='HTML'
        )
    finally:
        await state.clear()
        await cmd_job(message)