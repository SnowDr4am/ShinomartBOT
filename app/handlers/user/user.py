from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.handlers.main import user_router
import app.keyboards.user.user as kb
import app.database.requests as rq


@user_router.message(CommandStart())
async def cmd_start(message: Message):
    if await rq.check_user_by_id(message.from_user.id):
        text = (
            "<b>Привет!</b>\n\n"
            "Я бот шиномарта, который любит злить бухгалтера и делать для Вас скидки\n"
            "Вы находитесь в основном меню"
        )
        reply_markup = kb.main_menu
    else:
        text = (
            "<b>Привет!</b>\n\n"
            "Я бот шиномарта, который любит злить бухгалтера и делать для Вас скидки\n\n"
            "Для начала сотрудничества с нами, Вам необходимо зарегистрироваться"
        )
        reply_markup = kb.registration

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )


@user_router.callback_query(F.data == 'main_menu')
async def main_menu(callback: CallbackQuery):
    await callback.answer("")
    await callback.message.answer(
        text="<b>Привет!</b>\n\n"
        "Я бот шиномарта, который любит злить бухгалтера и делать для Вас скидки\n"
        "Вы находитесь в основном меню",
        parse_mode="HTML", reply_markup=kb.main_menu
    )


@user_router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):
    await callback.answer("")
    user_id = callback.from_user.id
    profile_data = await rq.get_user_profile(user_id)

    if profile_data:
        registration_date = profile_data['registration_date'].replace("-", ".")
        birthday_date = profile_data['birthday_date'].replace("-", ".")

        profile_message = (
            f"<b>👤 Личный кабинет пользователя</b>\n"
            f"<b>——————</b>\n\n"
            f"<b>🆔 Ваш ID:</b> <code>{profile_data['user_id']}</code>\n\n"
            f"<b>👋 Имя:</b> {profile_data['name']}\n\n"
            f"<b>📅 Дата регистрации:</b> {registration_date}\n\n"
            f"<b>📞 Номер телефона:</b> {profile_data['mobile_phone']}\n\n"
            f"<b>🎂 Дата рождения:</b> {birthday_date}\n\n"
            f"<b>💰 Бонусный баланс:</b> {profile_data['bonus_balance']} бонусов\n\n"
            f"<b>——————</b>\n\n"
            "<i>Если данные неверные или нужно обновить информацию, свяжитесь с поддержкой</i>"
        )
    else:
        profile_message = (
            "<b>Профиль не найден</b>\n\n"
            "<i>Пожалуйста, попробуйте позже или обратитесь в поддержку.</i>"
        )

    await callback.message.answer(profile_message, parse_mode="HTML", reply_markup=kb.profile)


@user_router.callback_query(F.data == 'history_purchase')
async def history_purchase(callback: CallbackQuery):
    await callback.answer("")
    user_id = callback.from_user.id

    transactions = await rq.get_last_10_transactions(user_id)

    if not transactions:
        await callback.message.answer("История покупок пуста")
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

    await callback.message.answer(history_message, parse_mode="HTML")