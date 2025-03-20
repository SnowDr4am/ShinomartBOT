from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State

from app.handlers.main import employee_router
from app.handlers.user.sched_handlers import update_channel_message
import app.keyboards.employee.employee as kb
import app.database.requests as rq
import app.database.ai_requests as ai_rq


class GetUserPhone(StatesGroup):
    mobile_phone = State()


@employee_router.message(F.text == '🗑️ Отменить запись')
async def remove_appointment_client(message: Message, state: FSMContext):
    try:
        await message.answer(
            "🆕 <b>Вы выбрали: Отменить запись клиенту</b>\n\n"
            "🔢 <b>Введите последние 4 цифры номера телефона</b> клиента:\n"
            "ℹ️ <i>Для выхода нажмите</i> <b>'отмена'</b>",
            parse_mode='HTML'
        )
        await state.set_state(GetUserPhone.mobile_phone)
    except Exception as e:
        await message.answer(
            "⚠️ <b>Ошибка:</b> Не удалось начать процесс. Попробуйте позже.",
            parse_mode='HTML'
        )
        print(f"Ошибка в remove_appointment_client: {e}")


@employee_router.message(GetUserPhone.mobile_phone)
async def send_phone_numbers(message: Message, state: FSMContext):
    user_input = message.text.strip()

    if "отмена" in user_input.lower():
        await state.clear()
        await message.answer(
            "❌ <b>Операция отменена</b> 🔄\n\n"
            "Вы вернулись в главное меню. Выберите действие для продолжения.",
            parse_mode='HTML'
        )
        return

    if not user_input.isdigit() or len(user_input) != 4:
        await message.answer(
            "⚠️ <b>Ошибка ввода!</b> 🚫\n\n"
            "🔢 Введите <u>ровно 4 цифры</u> (последние цифры номера телефона).\n"
            "Пример: <b>1234</b>",
            parse_mode='HTML'
        )
        return

    try:
        phone_numbers = await rq.get_phone_numbers_by_suffix(user_input)
        if not phone_numbers:
            await message.answer(
                "❌ <b>Номер не найден!</b> 🔍\n\n"
                "Проверьте введённые цифры или убедитесь, что клиент зарегистрирован.",
                parse_mode='HTML'
            )
            return

        keyboard = await kb.generate_phone_numbers_appointment(phone_numbers)
        await message.answer(
            "📱 <b>Выберите номер телефона клиента:</b>\n\n"
            "👇 Нажмите на номер из списка для продолжения:",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        await message.answer(
            "⚠️ <b>Ошибка:</b> Не удалось получить номера. Попробуйте позже.",
            parse_mode='HTML'
        )
        print(f"Ошибка в send_phone_numbers: {e}")


@employee_router.callback_query(F.data.startswith("appointment_phone"))
async def handle_phone_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    phone_number = callback.data.split(":")[1]

    try:
        user_data = await rq.get_user_by_phone(phone_number)
        if user_data:
            appointment = await ai_rq.get_active_appointment(user_data.user_id)
            appointment_info = (
                f"⏰ <b>Время записи:</b> {appointment.date_time.strftime('%H:%M %d.%m.%Y')}\n"
                f"🛠️ <b>Услуга:</b> {appointment.service.split('. Тип машины')[0]}"
            ) if appointment else "⏰ <b>Запись:</b> Отсутствует"

            user_info_message = (
                "📋 <b>Профиль клиента:</b>\n\n"
                f"👤 <b>Имя:</b> {user_data.name or 'Не указано'}\n"
                f"📞 <b>Номер телефона:</b> {user_data.mobile_phone}\n"
                f"💰 <b>Бонусный баланс:</b> {user_data.bonus_balance.balance if user_data.bonus_balance else 0} бонусов\n\n"
                f"<b>📋 Запись в сервис:</b>\n"
                f"{appointment_info}\n\n"
                "🔍 <i>Выберите действие:</i>"
            )
            keyboard = await kb.approved_remove_appointment_keyboard(user_data.user_id)
            await callback.message.edit_text(user_info_message, parse_mode='HTML', reply_markup=keyboard)
            await state.clear()
        else:
            await callback.message.edit_text(
                "❌ <b>Клиент не найден!</b> 😕\n\n"
                "Профиль с этим номером отсутствует в базе.",
                parse_mode='HTML'
            )
    except Exception as e:
        await callback.message.edit_text(
            "⚠️ <b>Ошибка:</b> Не удалось загрузить профиль. Попробуйте позже.",
            parse_mode='HTML'
        )
        print(f"Ошибка в handle_phone_selection: {e}")


@employee_router.callback_query(F.data.startswith("remove_appointment_approved"))
async def handle_remove_appointment(callback: CallbackQuery):
    await callback.answer()
    user_id = str(callback.data.split(":")[1])

    try:
        success = await ai_rq.cancel_appointment(user_id)
        if success:
            try:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text="❌ <b>Ваша запись отменена</b> сотрудником.\n\n"
                         "ℹ️ Если это ошибка, свяжитесь с нами! 📞",
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

            await callback.message.edit_text(
                "✅ <b>Запись успешно отменена!</b> 🎉\n\n"
                f"Клиент с ID {user_id} больше не записан.",
                parse_mode='HTML'
            )
            await update_channel_message(callback.bot)
        else:
            await callback.message.edit_text(
                "⚠️ <b>Ошибка:</b> Не удалось отменить запись.\n\n"
                "Возможно, запись уже отсутствует или произошла ошибка.",
                parse_mode='HTML'
            )
    except Exception as e:
        await callback.message.edit_text(
            "⚠️ <b>Ошибка:</b> Проблема при отмене записи. Попробуйте позже.",
            parse_mode='HTML'
        )
        print(f"Ошибка в handle_remove_appointment: {e}")