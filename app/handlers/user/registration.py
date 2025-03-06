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


class GetUserInfo(StatesGroup):
    name = State()
    mobile_phone = State()
    birthday = State()


@user_router.callback_query(F.data == 'registration')
async def registration(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await callback.message.edit_text(
        "📝 <b>Для регистрации мне необходимо собрать о Вас следующую информацию:</b>\n"
        "— 👤 <b>Ваше имя</b>\n"
        "— 📞 <b>Ваш номер телефона</b>\n"
        "— 🎂 <b>Дату рождения</b>\n\n",
        parse_mode="HTML"
    )
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
        if message.contact is not None:
            phone_number = message.contact.phone_number
            cleaned_number = re.sub(r'\D', '', phone_number)
        else:
            user_input = message.text
            if not user_input:
                await message.answer(
                    "⚠️ <b>Вы не ввели номер телефона.</b>",
                        parse_mode='HTML'
                )
                return

            cleaned_number = re.sub(r'\D', '', user_input)

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

        await state.set_state(GetUserInfo.birthday)
        await message.answer(
            "📅 <b>Напишите вашу дату рождения</b>\n"
            "Пример: <code>26.02.2025</code>",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )

    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer(
            "⚠️ <b>Произошла ошибка при обработке номера телефона.</b> Попробуйте ещё раз",
            parse_mode='HTML'
        )


@user_router.message(GetUserInfo.birthday)
async def get_birthday_date(message: Message, state: FSMContext):
    user_input = message.text.strip()

    try:
        cleaned_input = re.sub(r'[^0-9\.\-/]', '', user_input)

        date_formats = [
            "%Y.%m.%d", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"
        ]

        parsed_date = None
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(cleaned_input, date_format)
                break
            except ValueError:
                continue

        if not parsed_date:
            await message.answer("❌ <b>Некорректный формат даты.</b> Используйте ДД.ММ.ГГГГ.", parse_mode='HTML')
            return

        formatted_date = parsed_date.strftime("%d.%m.%Y")

        await state.update_data(birthday=formatted_date)

        data = await state.get_data()
        name = data.get("name")
        number = data.get("mobile_phone")

        birthday_date_obj = parsed_date.date()

        if await rq.set_user(message.from_user.id, datetime.now(), name, number, birthday_date_obj):
            await message.answer(
                f"✅ <b>Регистрация завершена.</b>\n"
                f"👤 <b>Имя:</b> {name}\n"
                f"📞 <b>Телефон:</b> {number}\n"
                f"🎂 <b>Дата рождения:</b> {formatted_date}",
                parse_mode='HTML'
            )

            await cmd_start(message)
        else:
            await message.answer("🚨 <b>Внутренняя ошибка.</b> Попробуйте позже.", parse_mode='HTML')
    except Exception as e:
        await message.answer("⚠️ <b>Ошибка обработки даты.</b> Попробуйте ещё раз.", parse_mode='HTML')
        print(f"Ошибка: {e}")