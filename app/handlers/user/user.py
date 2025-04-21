from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from app.handlers.employee.employee import handle_phone_selection_by_qr
from app.handlers.main import user_router
from app.servers.config import PHONE_NUMBER
import app.keyboards.user.user as kb
import app.database.requests as rq


@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if message.text:
        phone_number = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else None
    else:
        phone_number = None

    if phone_number:
        user_role = await rq.get_user_role(message.from_user.id)
        if not user_role or user_role not in ["Работник", "Администратор"]:
            pass
        else:
            qr = await rq.check_qr_code(phone_number)
            if not qr:
                await message.answer("⛔ <b>QR-код недействителен</b>\nИстёк срок действия 😔", parse_mode="HTML")
                return

            await handle_phone_selection_by_qr(message, phone_number, state)
            return

    if await rq.check_user_by_id(message.from_user.id):
        text = (
            "<b>Привет, друг!</b>\n\n"
            "<b>Я — твой личный помощник в шиномарте</b> 🚗💨\n\n"
            "Здесь ты можешь получить скидки, акции и все, что нужно для твоего удобства.\n\n"
            "Выбери нужный раздел из меню ниже 👇"
        )
        reply_markup = kb.main_menu
    else:
        text = (
            "<b>Привет!</b>\n\n"
            "<b>Я — твой личный помощник в шиномарте</b> 🚗💨\n\n"
            "Здесь ты можешь получить крутые скидки, акции и все, что нужно для твоего удобства 🎉\n\n"
            "Чтобы начать сотрудничество, просто пройди регистрацию — это займет всего пару минут ⏳"
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
    await callback.message.edit_text(
        text="<b>Привет, друг!</b>\n\n"
            "<b>Я — твой личный помощник в шиномарте</b> 🚗💨\n\n"
            "Здесь ты можешь получить скидки, акции и все, что нужно для твоего удобства.\n\n"
            "Выбери нужный раздел из меню ниже 👇",
        parse_mode="HTML", reply_markup=kb.main_menu
    )


@user_router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):
    await callback.answer("")
    user_id = callback.from_user.id
    profile_data = await rq.get_user_profile(user_id)

    if profile_data:
        registration_date = profile_data['registration_date'].replace("-", ".")

        profile_message = (
            f"<b>👤 Личный кабинет пользователя</b>\n"
            f"<b>——————</b>\n\n"
            f"<b>🆔 Ваш ID:</b> <code>{profile_data['user_id']}</code>\n\n"
            f"<b>👋 Имя:</b> {profile_data['name']}\n\n"
            f"<b>📅 Дата регистрации:</b> {registration_date}\n\n"
            f"<b>📞 Номер телефона:</b> {profile_data['mobile_phone']}\n\n"
            f"<b>💰 Бонусный баланс:</b> {profile_data['bonus_balance']} бонусов\n\n"
            f"<b>——————</b>\n\n"
            "<i>Если данные неверные или нужно обновить информацию, свяжитесь с поддержкой</i>"
        )
    else:
        profile_message = (
            "<b>❌ Профиль не найден</b>\n\n"
            "<i>😔 К сожалению, не удалось найти ваш профиль. Пожалуйста, попробуйте позже или свяжитесь с нашей поддержкой для помощи 📞.</i>"
        )

    await callback.message.edit_text(profile_message, parse_mode="HTML", reply_markup=kb.profile)


@user_router.callback_query(F.data == 'history_purchase')
async def history_purchase(callback: CallbackQuery):
    await callback.answer("")
    user_id = callback.from_user.id

    transactions = await rq.get_last_10_transactions(user_id)

    if not transactions:
        await callback.message.answer("🛒 История покупок пуста. \nВаши покупки появятся здесь, как только вы сделаете заказ! 😊",
                                      reply_markup=kb.delete_button_user)
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

    await callback.message.answer(history_message, parse_mode="HTML", reply_markup=kb.delete_button_user)


@user_router.callback_query(F.data == "delete_button_user")
async def delete_history_message(callback: CallbackQuery):
    await callback.answer()

    await callback.message.delete()


@user_router.callback_query(F.data == "contact")
async def contact_us(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        f"Номер телефона для связи с нами:\n"
        f"{PHONE_NUMBER}",
        parse_mode='HTML',
        reply_markup=kb.back_to_main_menu
    )