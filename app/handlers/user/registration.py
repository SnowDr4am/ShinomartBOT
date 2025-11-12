from aiogram import F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from datetime import datetime
import re

from app.handlers.user.user import cmd_start
from app.handlers.main import user_router
import app.keyboards.user.user as kb
import app.database.requests as rq
from config import CHANNEL_ID


class GetUserInfo(StatesGroup):
    name = State()
    mobile_phone = State()


@user_router.callback_query(F.data == 'registration')
async def registration(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    await callback.message.delete()
    await callback.message.answer(
        "🖊️ <b>Напишите, пожалуйста, Ваше имя</b>",
        parse_mode='HTML'
    )
    await state.set_state(GetUserInfo.name)

@user_router.message(GetUserInfo.name)
async def get_name(message: Message, state: FSMContext):
    user_input = message.text

    await state.update_data(name=user_input)

    await message.answer(
        "📱 <b>Напишите, пожалуйста, ваш номер телефона</b>",
        parse_mode='HTML',
        reply_markup=kb.get_phone_number
    )

    await state.set_state(GetUserInfo.mobile_phone)

@user_router.message(GetUserInfo.mobile_phone)
async def get_mobile_phone(message: Message, state: FSMContext):
    try:
        # Проверяем, что номер отправлен через кнопку (contact)
        if message.contact is None:
            # Если пользователь отправил текст вместо использования кнопки
            return await message.answer(
                "📱 <b>Пожалуйста, используйте кнопку для отправки номера телефона!</b>\n\n"
                "🔍 <b>Где найти кнопку?</b>\n"
                "Кнопка находится <b>справа от поля ввода текста</b> (внизу экрана).\n"
                "Нажмите на иконку 📎 (скрепка) или найдите большую кнопку с текстом "
                "<b>«ОТПРАВИТЬ НОМЕР ТЕЛЕФОНА»</b>.\n\n"
                "Кнопка автоматически отправит ваш номер телефона из настроек Telegram.",
                parse_mode='HTML',
                reply_markup=kb.get_phone_number
            )
        
        # Номер отправлен через кнопку
        phone_number = message.contact.phone_number
        cleaned_number = re.sub(r'\D', '', phone_number)

        if not cleaned_number or cleaned_number[0] not in ('7', '8'):
            await message.answer(
                "❌ <b>Некорректный формат номера.</b> Номер должен начинаться с 7 или 8.",
                parse_mode='HTML'
            )

            return

        if cleaned_number[0] == '7':
            cleaned_number = '8' + cleaned_number[1:]

        if len(cleaned_number) != 11:
            await message.answer(
                "❌ <b>Некорректная длина номера.</b> Номер должен содержать 11 цифр",
                parse_mode='HTML'
            )
            return

        if await rq.check_mobile_phone(cleaned_number):
            await message.answer(
                "🚫 <b>Номер телефона уже зарегистрирован.</b>",
                parse_mode='HTML'
            )
            return

        await state.update_data(mobile_phone=cleaned_number)

        data = await state.get_data()
        name = data.get("name")
        number = data.get("mobile_phone")
        user_id = message.from_user.id

        bonus_settings = await rq.get_bonus_system_settings()

        if await rq.set_user(user_id, datetime.now(), name, number, datetime.now(), bonus_settings['start_bonus_balance']):
            # Регистрация успешна - отправляем сообщение пользователю
            await message.answer(
                f"✅ <b>Регистрация завершена.</b>\n"
                f"👤 <b>Имя:</b> {name}\n"
                f"📞 <b>Телефон:</b> {number}\n",
                parse_mode='HTML',
                reply_markup=ReplyKeyboardRemove()
            )

            # Пытаемся отправить уведомление в канал (не критично, если не получится)
            try:
                user_link = f"@{message.from_user.username}" if message.from_user.username else f'<a href="tg://user?id={user_id}">{name}</a>'
                await message.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text = (
                        f"💎 <b>Новый пользователь в боте:</b>\n"
                        f"━━━━━━━━━━━━━━━━\n\n"
                        f"🔹 <b>Имя:</b> {name}\n\n"
                        f"🔹 <b>Телефон:</b> {number}\n\n"
                        f"🔹 <b>Профиль</b> {user_link}"
                    ),
                    parse_mode='HTML'
                )
            except Exception as channel_error:
                # Логируем ошибку отправки в канал, но не прерываем регистрацию
                print(f"⚠️ Не удалось отправить уведомление в канал: {channel_error}")

            await state.clear()
            await cmd_start(message, state)
        else:
            await message.answer("🚨 <b>Внутренняя ошибка.</b> Попробуйте позже.", parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
        await message.answer(
            "⚠️ <b>Произошла ошибка при обработке номера телефона.</b> Попробуйте ещё раз",
            parse_mode='HTML',
            reply_markup=kb.get_phone_number
        )