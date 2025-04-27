from aiogram import F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State

from app.servers.config import CHANNEL_ID
from app.handlers.main import employee_router
import app.keyboards.employee.employee as kb
import app.database.requests as rq


class GetUser(StatesGroup):
    mobile_phone = State()
    select_action = State()
    amount = State()
    bonus_balance = State()
    bonus_deduction = State()
    confirm_deduction = State()
    cashback = State()
    max_debit = State()



@employee_router.message(Command("job"))
async def cmd_employee(message: Message):
    await message.answer(
        "<b>📋 Вы перешли в меню работника!</b>\n\n"
        "<i>👉 Все взаимодействие будет происходить через кнопки ниже.</i>\n"
        "<u>Нажмите на одну из кнопок, чтобы продолжить.</u>",
        parse_mode='HTML',
        reply_markup=kb.main_menu
    )


@employee_router.callback_query(F.data == "employee_main_menu")
async def callback_employee(callback: CallbackQuery):
    await callback.answer(
        "<b>📋 Вы перешли в меню работника!</b>\n\n"
        "<i>👉 Все взаимодействие будет происходить через кнопки ниже.</i>\n"
        "<u>Нажмите на одну из кнопок, чтобы продолжить.</u>",
        parse_mode='HTML',
        reply_markup=kb.main_menu
    )


@employee_router.message(F.text == '💳 Новая транзакция')
async def add_bonus(message: Message, state: FSMContext):
    await message.answer(
        "🆕 <b>Вы выбрали 'Новая транзакция'</b> 💸\n\n"
        "🔢 Пожалуйста, введите <b>последние 4 цифры номера телефона</b> пользователя:\n"
        "<i>Для выхода из этого меню нажмите <b>'отмена'</b></i>",
        parse_mode='HTML'
    )

    await state.set_state(GetUser.mobile_phone)


@employee_router.message(GetUser.mobile_phone)
async def send_phone_numbers(message: Message, state: FSMContext):
    user_input = message.text

    if "отмена" in user_input.lower():
        await state.clear()
        await message.answer(
            "❌ <b>Операция отменена</b> 🔄\n\n"
            "Вы успешно вышли из текущего процесса. Если хотите начать снова, просто выберите нужное действие."
            , parse_mode='HTML'
        )
        return

    if not user_input.isdigit() or len(user_input) != 4:
        await message.answer(
            "⚠️ <b>Некорректный ввод!</b> 🚫\n\n"
            "Пожалуйста, введите <b>последние 4 цифры</b> номера телефона пользователя.\n"
            "Убедитесь, что введены только цифры и их ровно 4."
            , parse_mode='HTML'
        )

        return

    phone_numbers = await rq.get_phone_numbers_by_suffix(user_input)

    if not phone_numbers:
        await message.answer(
            "❌ <b>Номер телефона не найден!</b> 🔍\n\n"
            "Проверьте введенные данные и попробуйте снова. Если проблема сохраняется, возможно, номер отсутствует в базе."
            , parse_mode='HTML'
        )

        return

    keyboard = await kb.generate_phone_numbers_keyboard(phone_numbers)
    await message.answer(
        "📱 <b>Выберите номер телефона:</b> \n\n"
        "Пожалуйста, выберите номер из предложенного списка, чтобы продолжить.",
        parse_mode='HTML',
        reply_markup=keyboard
    )


@employee_router.callback_query(F.data.startswith("cancel"))
async def handle_phone_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.answer(
        "❌ <b>Операция отменена</b>\n\n"
        "Вы успешно отменили текущую операцию. Если нужно, вы можете начать заново.",
        parse_mode='HTML'
    )

    await state.clear()


@employee_router.callback_query(F.data.startswith("select_phone"))
async def handle_phone_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    phone_number = callback.data.split(":")[1]

    user_data = await rq.get_user_by_phone(phone_number)

    if user_data:
        user_info_message = (
            "📋 <b>Профиль пользователя:</b>\n\n"
            f"👤 <b>Имя:</b> {user_data.name}\n"
            f"📞 <b>Номер телефона:</b> {user_data.mobile_phone}\n"
            f"💰 <b>Бонусный баланс:</b> {user_data.bonus_balance.balance} бонусов\n\n"
            "🔍 <i>Пожалуйста, выберите действие ниже.</i>"
        )
        keyboard = await kb.transaction_profile_keyboard(user_data.user_id)
        await callback.message.edit_text(user_info_message, parse_mode='HTML', reply_markup=keyboard)

        await state.update_data(phone_number=phone_number)
        await state.update_data(bonus_balance=user_data.bonus_balance.balance)

        await state.set_state(GetUser.select_action)
    else:
        await callback.message.answer(
            "❌ <b>Профиль пользователя не найден</b>",
            parse_mode='HTML'
        )
        return


async def handle_phone_selection_by_qr(message, phone_number, state: FSMContext):
    user_data = await rq.get_user_by_phone(phone_number)
    if user_data:
        user_info_message = (
            "📋 <b>Профиль пользователя:</b>\n\n"
            f"👤 <b>Имя:</b> {user_data.name}\n"
            f"📞 <b>Номер телефона:</b> {user_data.mobile_phone}\n"
            f"💰 <b>Бонусный баланс:</b> {user_data.bonus_balance.balance} бонусов\n\n"
            "🔍 <i>Пожалуйста, выберите действие ниже.</i>"
        )
        await message.delete()
        keyboard = await kb.transaction_profile_keyboard(user_data.user_id)
        await message.answer(user_info_message, parse_mode='HTML', reply_markup=keyboard)

        await state.update_data(phone_number=phone_number)
        await state.update_data(bonus_balance=user_data.bonus_balance.balance)

        await state.set_state(GetUser.select_action)
    else:
        await message.answer(
            "❌ <b>Профиль пользователя не найден</b>",
            parse_mode='HTML'
        )
        return


@employee_router.callback_query(GetUser.select_action, F.data.startswith("transaction:"))
async def handle_action_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    action = callback.data.split(":")[1]

    if action == "cancel":
        await state.clear()
        await callback.message.answer(
            "❌ <b>Операция отменена</b> 🔄\n\n"
            "Вы успешно вышли из текущего процесса. Если хотите начать снова, просто выберите нужное действие."
            , parse_mode='HTML'
        )
        return

    data = await state.get_data()
    phone_number = data.get("phone_number")

    await state.update_data(select_action=action)

    if action == 'add':
        await callback.message.edit_text(
            f"💳 <b>Вы выбрали пополнение бонусов для номера:</b> {phone_number}\n"
            "💰 <b>Введите сумму покупки:</b>\n\n"
            "🔍 <i>Для отмены операции нажмите или напишите 'отмена'</i>",
            parse_mode='HTML'
        )
        await state.set_state(GetUser.amount)
    elif action == 'remove':
        await callback.message.edit_text(
            f"❌ <b>Вы выбрали списание бонусов для номера:</b> {phone_number}\n"
            "💸 <b>Введите сумму покупки:</b>\n\n"
            "🔍 <i>Для отмены операции нажмите или напишите 'отмена'</i>",
            parse_mode='HTML'
        )

        await state.set_state(GetUser.amount)


@employee_router.message(GetUser.amount)
async def handle_amount_input(message: Message, state: FSMContext):
    user_input = message.text.strip()

    if "отмена" in user_input.lower():
        await state.clear()
        await message.answer(
            "❌ <b>Операция отменена</b> 🔄\n\n"
            "Вы успешно вышли из текущего процесса. Если хотите начать снова, просто выберите нужное действие."
            , parse_mode='HTML'
        )
        return

    try:
        amount = float(user_input)

        if amount <= 0:
            await message.answer("⚠️ <b>Введите положительное число:</b>", parse_mode='HTML')
    except Exception as e:
        await message.answer("❌ <b>Некорректный ввод.</b> Пожалуйста, введите <b>положительное число</b>.", parse_mode='HTML')
        return

    data = await state.get_data()
    phone_number = data.get("phone_number")
    action = data.get("select_action")
    bonus_balance = data.get("bonus_balance")

    current_bonus_settings = await rq.get_bonus_system_settings()
    check_vip_client = await rq.check_vip_client(phone_number)
    if check_vip_client:
        cashback = current_bonus_settings["vip_cashback"]/100
    else:
        cashback = current_bonus_settings["cashback"]/100
    max_debit = current_bonus_settings["max_debit"]/100

    await state.update_data(amount=amount, cashback=cashback, max_debit=max_debit)

    user_data = await rq.get_user_by_phone(phone_number)

    if not user_data:
        await message.answer("⚠️ <b>Профиль пользователя не найден.</b>", parse_mode='HTML')
        await state.clear()
        return

    if action == 'add':
        amount_bonus = amount * cashback
        success = await rq.set_bonus_balance(user_data.user_id, "add", amount_bonus, amount, message.from_user.id)
        if success:
            await state.clear()

            await send_report_to_channel(
                bot=message.bot,
                transaction_type=action,
                user_data=user_data,
                employee_id=message.from_user.id,
                amount=amount,
                bonus_amount=amount_bonus
            )

            await message.answer(
                f"🎉 <b>Начислено {amount_bonus:.2f} бонусов</b> пользователю {user_data.name} 🎁",
                parse_mode='HTML',
                reply_markup=kb.main_menu
            )
            await message.bot.send_message(
                chat_id=user_data.user_id,
                text=(
                    f"<b>🎉 Вам начислено {amount_bonus:.2f} бонусов!</b>\n"
                    f"💰 За покупку на сумму <b>{amount} руб.</b>\n\n"
                    f"👇 <b>Оцените работу нашего сотрудника прямо сейчас!</b> 👇"
                ),
                reply_markup=kb.assessment,
                parse_mode='HTML'
            )
            check_vote_status = await rq.get_user_vote_history(user_data.user_id)
            if check_vote_status:
                bonus_system = await rq.get_bonus_system_settings()
                await message.bot.send_message(
                    chat_id=user_data.user_id,
                    text=(
                        "🎉 <b>У нас действует акция!</b> 🎉\n\n"
                        f"💎 <b>За каждый положительный отзыв</b> мы начисляем <b>{bonus_system['voting_bonus']} бонусов</b> на ваш баланс!\n"
                        "🔥 <b>Не упустите шанс получить больше!</b>"
                    ),
                    reply_markup=kb.approved_voting,
                    parse_mode='HTML'
                )
        else:
            await message.answer(
                "⚠️ <b>Возникла ошибка при зачислении бонусов</b> 😞",
                parse_mode='HTML'
            )
    elif action == 'remove':
        max_bonus_deduction = amount * max_debit
        if bonus_balance <= max_bonus_deduction:
            finally_bonus = bonus_balance
        else:
            finally_bonus = max_bonus_deduction
        await state.update_data(bonus_deduction=finally_bonus)
        await message.answer(
            f"💸 <b>Вы можете списать максимум {finally_bonus} бонусов</b> с аккаунта пользователя",
            reply_markup=kb.confirm_transaction,
            parse_mode='HTML'
        )
        await state.set_state(GetUser.confirm_deduction)


@employee_router.callback_query(GetUser.confirm_deduction, F.data.startswith("confirm:"))
async def confirm_deduction(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    action = callback.data.split(":")[1]

    if action == "cancel":
        await state.clear()
        await callback.message.answer(
            "❌ <b>Операция отменена</b> 🔄\n\n"
            "Вы успешно вышли из текущего процесса. Если хотите начать снова, просто выберите нужное действие."
            , parse_mode='HTML'
        )
        return

    data = await state.get_data()
    phone_number = data.get("phone_number")
    bonus_deduction = data.get("bonus_deduction")
    amount = data.get("amount")
    cashback = data.get("cashback")

    user_data = await rq.get_user_by_phone(phone_number)

    if not user_data:
        await callback.message.answer("⚠️ <b>Профиль пользователя не найден.</b>", parse_mode='HTML')
        await state.clear()
        await callback.answer()
        return

    if action == 'no':
        amount_bonus = amount * cashback
        success = await rq.set_bonus_balance(user_data.user_id, "add", amount_bonus, amount, callback.from_user.id)
        if success:

            await send_report_to_channel(
                bot=callback.bot,
                transaction_type="add",
                user_data=user_data,
                employee_id=callback.from_user.id,
                amount=amount,
                bonus_amount=amount_bonus
            )

            await callback.message.edit_text(
                f"🎉 <b>Начислено {amount_bonus:.2f} бонусов</b> пользователю {user_data.name}",
                parse_mode='HTML'
            )
            await callback.bot.send_message(
                chat_id=user_data.user_id,
                text=(
                    f"<b>🎉 Вам начислено {amount_bonus:.2f} бонусов!</b>\n"
                    f"💰 За покупку на сумму <b>{amount} руб.</b>\n\n"
                    f"👇 <b>Оцените работу нашего сотрудника прямо сейчас!</b> 👇"
                ),
                reply_markup=kb.assessment,
                parse_mode='HTML'
            )
            check_vote_status = await rq.get_user_vote_history(user_data.user_id)
            if check_vote_status:
                bonus_system = await rq.get_bonus_system_settings()
                await callback.bot.send_message(
                    chat_id=user_data.user_id,
                    text=(
                        "🎉 <b>У нас действует акция!</b> 🎉\n\n"
                        f"💎 <b>За каждый положительный отзыв</b> мы начисляем <b>{bonus_system['voting_bonus']} бонусов</b> на ваш баланс!\n"
                        "🔥 <b>Не упустите шанс получить больше!</b>"
                    ),
                    reply_markup=kb.approved_voting,
                    parse_mode='HTML'
                )
            await state.clear()

            await callback_employee(callback)
        else:
            await callback.message.answer(
                "❗️ <b>Возникла ошибка при зачислении бонусов</b>.",
                parse_mode='HTML'
            )
    else:
        success = await rq.set_bonus_balance(user_data.user_id, "remove", bonus_deduction, amount, callback.from_user.id)
        if success:
            report_amount = amount-bonus_deduction
            await send_report_to_channel(
                bot=callback.bot,
                transaction_type="remove",
                user_data=user_data,
                employee_id=callback.from_user.id,
                amount=report_amount,
                bonus_amount=bonus_deduction
            )

            await callback.message.edit_text(
                f"💳 <b>Списано {bonus_deduction:.2f} бонусов</b> с аккаунта пользователя {user_data.name}\n"
                f"💰 <b>Итоговая цена для клиента:</b> {amount - bonus_deduction}",
                parse_mode='HTML'
            )
            await callback.bot.send_message(
                chat_id=user_data.user_id,
                text=(
                    f"<b>❌ У вас списано {bonus_deduction:.2f} бонусов!</b>\n"
                    f"💳 За покупку на сумму <b>{amount} руб.</b>\n\n"
                    f"👇 <b>Оцените работу нашего сотрудника прямо сейчас!</b> 👇"
                ),
                reply_markup=kb.assessment,
                parse_mode='HTML'
            )
            check_vote_status = await rq.get_user_vote_history(user_data.user_id)
            if check_vote_status:
                bonus_system = await rq.get_bonus_system_settings()
                await callback.bot.send_message(
                    chat_id=user_data.user_id,
                    text=(
                        "🎉 <b>У нас действует акция!</b> 🎉\n\n"
                        f"💎 <b>За каждый положительный отзыв</b> мы начисляем <b>{bonus_system['voting_bonus']} бонусов</b> на ваш баланс!\n"
                        "🔥 <b>Не упустите шанс получить больше!</b>"
                    ),
                    reply_markup=kb.approved_voting,
                    parse_mode='HTML'
                )
            await state.clear()

            await callback_employee(callback)
        else:
            await callback.message.answer(
                "❗️ <b>Возникла ошибка при списании бонусов</b>.",
                parse_mode='HTML'
            )

async def send_report_to_channel(
        bot: Bot,
        transaction_type,
        user_data,
        employee_id,
        amount,
        bonus_amount
):
    employee_data = await rq.get_user_by_tg_id(employee_id)

    user_profile_link = f'<a href="tg://user?id={user_data.user_id}">{user_data.name}</a>'
    employee_profile_link = f'<a href="tg://user?id={employee_id}">{employee_data.name}</a>'

    if transaction_type == "add":
        message_text = (
            "❇️ <b>Пополнение баллов:</b>\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"🔹<b>Пользователь:</b> {user_profile_link}\n\n"
            f"🔹<b>Номер телефона:</b> {user_data.mobile_phone}\n\n"
            f"🔹<b>Сумма покупки:</b> 🇷🇺{amount:.2f} рублей\n\n"
            f"🔹<b>Количество начисленных бонусов:</b> {bonus_amount:.2f} бонусов\n\n"
            f"🔹<b>Мастер:</b> {employee_profile_link}"
        )
    else:
        message_text = (
            "⛔️ <b>Списание баллов:</b>\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"🔹<b>Пользователь:</b> {user_profile_link}\n\n"
            f"🔹<b>Номер телефона:</b> {user_data.mobile_phone}\n\n"
            f"🔹<b>Цена для клиента:</b> 🇷🇺{amount:.2f} рублей\n\n"
            f"🔹<b>Количество списанных бонусов:</b> {bonus_amount:.2f} бонусов\n\n"
            f"🔹<b>Мастер:</b> {employee_profile_link}"
        )

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=message_text,
        parse_mode='HTML',
        disable_web_page_preview=True
    )